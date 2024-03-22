#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import sys
import os
import logging
from enum import Enum
from typing import Dict, List, Any, Optional

import astypes

import astroid
import astroid.nodes.scoped_nodes.scoped_nodes as astroid_nodes
import astroid.bases as astroid_bases
from astroid.nodes import node_classes, NodeNG
from astroid.modutils import _has_init
from astgraph.graphtheory import convert_to_list


_LOGGER = logging.getLogger(__name__)


# ============================================


def get_top_node(astroid_node: NodeNG):
    while astroid_node.parent:
        astroid_node = astroid_node.parent
    return astroid_node


def get_message(message: str, astroid_node: NodeNG):
    module_node = get_top_node(astroid_node)
    _LOGGER.error(
        "unhandled node in file %s(%s):\n%s", module_node.file, astroid_node.lineno, astroid_node.parent.repr_tree()
    )
    return f"{message} (node {type(astroid_node)})"


def get_type(astroid_node: NodeNG) -> str:
    node_astype = astypes.get_type(astroid_node)
    if not node_astype:
        return None
    return node_astype.annotation


def infer_node(astroid_node: NodeNG):
    try:
        return next(astroid_node.infer())
    except astroid.exceptions.InferenceError:
        # no inference succeed
        return None


def infer_type(astroid_node: NodeNG) -> Optional[NodeNG]:
    try:
        inferred = next(astroid_node.infer())
        if not inferred:
            return None
        # if isinstance(inferred, BoundMethod):
        #     caller = astroid_node.expr
        #     inferred_result = inferred.infer_call_result(caller)
        #     inferred_value = next(inferred_result)
        #     return unpack_proxy(inferred_value)
        if isinstance(inferred, astroid_bases.Proxy):
            return unpack_proxy(inferred)
        if isinstance(inferred, NodeNG):
            return inferred
        raise RuntimeError(f"unhandled type: {type(inferred)}")
    except astroid.exceptions.InferenceError as exc:
        # no inference succeed
        _LOGGER.warning("unable to infer: %s", exc)
        return None


def unpack_proxy(inferred):
    while inferred:
        if isinstance(inferred, astroid_bases.Proxy):
            inferred = inferred._proxied  # pylint: disable=W0212
            continue
        if isinstance(inferred, NodeNG):
            return inferred
        raise RuntimeError(f"unhandled type: {type(inferred)}")
    return None


# ============================================


class DefItemType(Enum):
    MODULE = "module"
    CLASS = "class"
    DEF_METHOD = "method"  # defined method
    MEMBER = "member"  # free function, method or attribute


class DefItem:
    def __init__(self, name: str, item_type: DefItemType, astroid_node):
        self.node_id = id(astroid_node)
        self.type: DefItemType = item_type
        self.parent = None
        self.name = name
        self.items: List[Any] = []  # children
        self.type_hint: Optional[DefItem] = None  # member type hint

    @property
    def info(self):
        return (self.get_full_name(), self.type)

    def is_module(self) -> bool:
        return self.type == DefItemType.MODULE

    def is_method(self) -> bool:
        return self.type == DefItemType.DEF_METHOD

    def is_field(self) -> bool:
        return self.type == DefItemType.MEMBER

    def append(self, item):
        self.items.append(item)
        item.parent = self

    def get_namespace(self):
        if not self.parent:
            return ""
        return self.parent.get_full_name()

    def get_name(self):
        return self.name

    def get_full_name(self):
        full_name = self.get_name()
        parent = self.parent
        while parent:
            par_name = parent.get_name()
            full_name = f"{par_name}.{full_name}"
            parent = parent.parent
        return full_name

    def get_filename(self):
        if not self.parent:
            return ""
        return self.parent.get_filename()

    def get_child(self, name):
        for item in self.items:
            if item.name == name:
                return item
        return None

    def to_string(self):
        return f"({self.name}, {self.type})"

    def __repr__(self):
        full_name = self.get_full_name()
        hex_id = f"0x{id(self):0x}"
        return f"<{full_name}, {self.type} {hex_id}>"


class ModuleItem(DefItem):
    def __init__(self, name: str, astroid_node, namespace=""):
        super().__init__(name, DefItemType.MODULE, astroid_node)
        self.namespace = namespace
        self.filename = None

    def get_namespace(self):
        return self.namespace

    def get_filename(self):
        return self.filename


# ============================================


class ItemContainer:
    def __init__(self):
        self.mod_dict = {}
        self.def_items: List[DefItem] = []  # list of all def items
        self.use_dict: Dict[DefItem, List[DefItem]] = {}
        self.astroid_item_dict: Dict[int, DefItem] = {}  # map astroid node (id) to def item
        self.astroid_node_dict: Dict[int, NodeNG] = {}

    def add_mod(self, mod: astroid_nodes.Module):
        if mod.name in self.mod_dict:
            return False
        self.mod_dict[mod.name] = mod
        return True

    def get_def_list(self):
        ret_list = []
        for def_item in self.def_items:
            ret_list.append(def_item.info)
        return ret_list

    def get_def_dict(self):
        flat_list = convert_to_list(self.def_items, lambda item: item.items)
        def_dict = {}
        for item in flat_list:
            def_dict[item] = item.items
        return def_dict

    def get_use_list(self):
        ret_list = []
        for def_key, def_list in self.use_dict.items():
            for def_item in def_list:
                ret_list.append((def_key.get_full_name(), def_item.get_full_name()))
        return ret_list

    def create_def(self, name: str, def_type: DefItemType, astroid_node: NodeNG) -> DefItem:
        item: DefItem = None
        if def_type == DefItemType.MODULE:
            item = ModuleItem(name, astroid_node)
        else:
            item = DefItem(name, def_type, astroid_node)
        if astroid_node is not None:
            node_id = id(astroid_node)
            self.astroid_item_dict[node_id] = item
            self.astroid_node_dict[node_id] = astroid_node
        return item

    def create_module_def(self, name: str, astroid_node: NodeNG) -> ModuleItem:
        item = ModuleItem(name, astroid_node)
        if astroid_node is not None:
            node_id = id(astroid_node)
            self.astroid_item_dict[node_id] = item
            self.astroid_node_dict[node_id] = astroid_node
        return item

    def append_def(self, def_item: DefItem):
        if def_item.type == DefItemType.MODULE:
            # add top level item - module (does not have parent scope)
            _LOGGER.debug("append def: %s", def_item.get_full_name())
            self.def_items.append(def_item)
            return

        node_id = def_item.node_id
        parent_def = self.find_scope_by_id(node_id)
        if not parent_def:
            raise RuntimeError(f"missing scope for item {def_item.name}")
        self.append_def_parent(parent_def, def_item)

    def append_def_parent(self, parent: DefItem, def_item: DefItem):
        _LOGGER.debug("append def: %s", def_item.get_full_name())
        self.def_items.append(def_item)
        parent.append(def_item)

    def append_use(self, user_item: DefItem, use_item: DefItem):
        # here we are sure that 'user_item' and 'use_item' is already added to def structures
        uses_list = self.use_dict.get(user_item)
        if uses_list is None:
            uses_list = []
            self.use_dict[user_item] = uses_list
        if use_item not in uses_list:
            _LOGGER.debug("append use: %s -> %s", user_item.get_full_name(), use_item.get_full_name())
            uses_list.append(use_item)

    def find_def_item(self, astroid_node: NodeNG) -> Optional[DefItem]:
        node_id = id(astroid_node)
        return self.astroid_item_dict.get(node_id)

    def find_scope(self, astroid_node: NodeNG) -> Optional[DefItem]:
        parent_node: NodeNG = astroid_node.parent
        while parent_node:
            parent_def = self.find_def_item(parent_node)
            if parent_def:
                return parent_def
            parent_node = parent_node.parent
        return None

    def find_parent_scope_def(self, astroid_node: NodeNG) -> Optional[DefItem]:
        scope_node = astroid_node
        while scope_node:
            parent_node = scope_node.parent  # scope returns self
            if parent_node is None:
                # no parent scope
                return None
            scope_node = parent_node.scope()
            scope_def = self.find_def_item(scope_node)
            if scope_def is not None:
                return scope_def
        return None

    def find_scope_by_id(self, node_id: int) -> Optional[DefItem]:
        item_node: NodeNG = self.astroid_node_dict.get(node_id)
        if not item_node:
            return None
        return self.find_scope(item_node)

    def find_scope_class(self, astroid_node: NodeNG) -> Optional[DefItem]:
        parent_node: NodeNG = astroid_node.parent
        while parent_node:
            parent_def = self.find_def_item(parent_node)
            if parent_def and parent_def.type == DefItemType.CLASS:
                return parent_def
            parent_node = parent_node.parent
        return None

    # name is type name or variable name
    def find_in_scope(self, scope_node, name) -> Optional[NodeNG]:
        if scope_node is None:
            return None
        while scope_node:
            found_type_node = scope_node.locals.get(name)
            if found_type_node:
                # found node
                found_node = found_type_node[0]
                if isinstance(found_node, node_classes.Import):
                    mod_name = found_node.names[0][0]
                    mod_node = self.mod_dict.get(mod_name)
                    return self.find_in_scope(mod_node, name)
                if isinstance(found_node, node_classes.ImportFrom):
                    mod_name = found_node.modname
                    mod_node = self.mod_dict.get(mod_name)
                    return self.find_in_scope(mod_node, name)
                return found_node
            parent_node = scope_node.parent  # scope returns self
            if parent_node is None:
                # no parent scope
                break
            scope_node = parent_node.scope()

        # no item found up to module - check other imported modules
        return self.mod_dict.get(name)


# ============================================


class BaseParser:
    def __init__(self, container: ItemContainer = None):
        if container is None:
            container = ItemContainer()
        self.items = container

    def analyze(self, astroid_node: astroid_nodes.Module):
        self._visit(astroid_node)

    def _visit(self, astroid_node):
        # implement if needed
        pass

    def _visit_children(self, astroid_node):
        for child in astroid_node.get_children():
            self._visit(child)

    def _visit_list(self, nodes_list):
        for child in nodes_list:
            self._visit(child)


# ============================================


class DefParser(BaseParser):
    def _visit(self, astroid_node):
        _LOGGER.debug("visiting item: %s", type(astroid_node))

        if isinstance(astroid_node, astroid_nodes.Module):
            self.visit_module(astroid_node)
            return
        if isinstance(astroid_node, astroid_nodes.ClassDef):
            self.visit_classdef(astroid_node)
            return
        if isinstance(astroid_node, astroid_nodes.FunctionDef):
            self.visit_functiondef(astroid_node)
            return

        self._visit_children(astroid_node)

    def _visit_children(self, astroid_node):
        for child in astroid_node.get_children():
            self._visit(child)

    # ============================================================

    def visit_module(self, astroid_node):
        _LOGGER.debug("visiting Module %s", astroid_node.name)
        mod_name = astroid_node.name
        mod_name = os.path.basename(mod_name)
        if mod_name.endswith(".py"):
            mod_name = mod_name[:-3]

        moduledef: ModuleItem = self.items.create_module_def(mod_name, astroid_node)
        moduledef.filename = astroid_node.file
        self.items.append_def(moduledef)

        self._visit_children(astroid_node)

    def visit_classdef(self, astroid_node):
        _LOGGER.debug("visiting ClassDef %s", astroid_node.name)
        if self.items.find_def_item(astroid_node):
            # already defined - happens in "forward declarations"
            _LOGGER.debug("%s already handled", astroid_node.name)
            return

        class_name = astroid_node.name
        classdef = self.items.create_def(class_name, DefItemType.CLASS, astroid_node)
        self.items.append_def(classdef)

        self._visit_children(astroid_node)

    def visit_functiondef(self, astroid_node):
        _LOGGER.debug("visiting FunctionDef %s", astroid_node.name)
        if self.items.find_def_item(astroid_node):
            # already defined - happens in "forward declarations"
            _LOGGER.debug("%s already handled", astroid_node.name)
            return

        func_name = astroid_node.name
        functiondef = self.items.create_def(func_name, DefItemType.DEF_METHOD, astroid_node)
        self.items.append_def(functiondef)

        self._visit_children(astroid_node)


# ============================================


class UseParser(BaseParser):
    def _visit(self, astroid_node):
        _LOGGER.debug("visiting item: %s", type(astroid_node))

        if isinstance(astroid_node, node_classes.Call):
            self.visit_call(astroid_node)
            return
        if isinstance(astroid_node, node_classes.Keyword):
            self.visit_keyword(astroid_node)
            return
        if isinstance(astroid_node, node_classes.AssignName):
            self.visit_assignname(astroid_node)
            return
        if isinstance(astroid_node, node_classes.AssignAttr):
            self.visit_assignattr(astroid_node)
            return
        if isinstance(astroid_node, node_classes.AnnAssign):
            self.visit_annassign(astroid_node)
            return
        if isinstance(astroid_node, node_classes.Attribute):
            self.visit_attribute(astroid_node)
            return

        self._visit_children(astroid_node)

    def _visit_children(self, astroid_node):
        for child in astroid_node.get_children():
            self._visit(child)

    # ============================================

    def visit_call(self, astroid_node):
        _LOGGER.debug("visiting Call")

        def_list = self._resolve_attribute(astroid_node)
        if def_list:
            user_def = self.items.find_parent_scope_def(astroid_node)
            if not user_def:
                _LOGGER.debug("invalid node:\n%s", astroid_node.scope().repr_tree())
                raise RuntimeError("unable to get user def item")
            for def_item in def_list[:-1]:
                if not def_item:
                    # happens e.g. in case of direct imports
                    continue
                if def_item.type == DefItemType.MODULE:
                    continue
                if def_item.type == DefItemType.CLASS:
                    continue
                self.items.append_use(user_def, def_item)
            last_item = def_list[-1]
            if last_item:
                # None can occur for function calls (e.g. 'print')
                last_callable = self._get_callable(last_item)
                self.items.append_use(user_def, last_callable)

        self._visit_list(astroid_node.args)
        self._visit_list(astroid_node.keywords)

    def visit_keyword(self, astroid_node):
        _LOGGER.debug("visiting Keyword")
        value_node = astroid_node.value
        def_list = self._resolve_attribute(value_node)
        if def_list:
            user_def = self.items.find_parent_scope_def(value_node)
            if not user_def:
                _LOGGER.debug("invalid node:\n%s", value_node.scope().repr_tree())
                raise RuntimeError("unable to get user def item")
            for def_item in def_list[:-1]:
                if not def_item:
                    # happens e.g. in case of direct imports
                    continue
                if def_item.type == DefItemType.MODULE:
                    continue
                if def_item.type == DefItemType.CLASS:
                    continue
                self.items.append_use(user_def, def_item)
            last_item = def_list[-1]
            if last_item:
                # None can occur for function calls (e.g. 'print')
                self.items.append_use(user_def, last_item)

    def visit_assignname(self, astroid_node):
        # assigning value (expression) to object's attribute
        _LOGGER.debug("visiting AssignName")

        scope_node = astroid_node.scope()
        if hasattr(scope_node, "type"):
            scope_type = scope_node.type
        else:
            # module does not have "type" attribute
            scope_type = "module"

        if scope_type == "class":
            # class field
            scope_def: Optional[DefItem] = self.items.find_def_item(scope_node)
            if scope_def is None:
                raise RuntimeError("unable to find definition item")
            assign_name = astroid_node.name
            child = scope_def.get_child(assign_name)
            if child is None:
                child = self.items.create_def(assign_name, DefItemType.MEMBER, astroid_node)
                self.items.append_def(child)
            # class scope definitions - do not add to uses
            # self.items.append_use(child)
            return

        self._visit_children(astroid_node)

    def visit_assignattr(self, astroid_node):
        # assigning value (expression) to object's attribute
        _LOGGER.debug("visiting AssignAttr")

        attr_expr = astroid_node.expr
        if isinstance(attr_expr, node_classes.Name):
            attr_name = astroid_node.attrname
            self._handle_name(attr_expr, attr_name)
            return

        self._visit_children(astroid_node)

    def visit_annassign(self, astroid_node):
        # assigning value (expression) to object's attribute
        _LOGGER.debug("visiting AnnAssign")

        self._visit_children(astroid_node)

        attr_list = self._resolve_attribute(astroid_node.target)
        if not attr_list:
            return
        last_item: DefItem = attr_list[-1]
        if not last_item:
            return
        inferred_hint = infer_type(astroid_node.annotation)
        if not inferred_hint:
            return
        hint_def = self.items.find_def_item(inferred_hint)
        last_item.type_hint = hint_def

    def visit_attribute(self, astroid_node):
        # read value from object's attribute
        _LOGGER.debug("visiting Attribute")

        def_list = self._resolve_attribute(astroid_node)
        if def_list:
            user_def = self.items.find_parent_scope_def(astroid_node)
            if not user_def:
                _LOGGER.debug("invalid node:\n%s", astroid_node.scope().repr_tree())
                raise RuntimeError("unable to get user def item")
            for def_item in def_list[:-1]:
                if not def_item:
                    # happens e.g. in case of direct imports
                    continue
                if def_item.type == DefItemType.MODULE:
                    continue
                if def_item.type == DefItemType.CLASS:
                    continue
                self.items.append_use(user_def, def_item)
            last_item = def_list[-1]
            if last_item:
                # None can occur for function calls (e.g. 'print')
                self.items.append_use(user_def, last_item)

    # if given then 'attribute_name' is name of member of object defined by 'name_node'
    # if 'attribute_name' is empty, then 'name_node' is name of free function
    def _handle_name(self, name_node: NodeNG, attribute_name: Optional[str]) -> bool:
        if attribute_name:
            # name_node - describes object
            # attribute_name - describes object's member
            type_def_item: Optional[DefItem] = self._find_type_def(name_node, name_node.name)
            if type_def_item is None:
                _LOGGER.warning("unable to find name item of type %s", name_node.name)
                return False
            if type_def_item.type != DefItemType.CLASS:
                _LOGGER.warning("unable to handle Name type")
                return False

            user_def = self.items.find_scope(name_node)
            if not user_def:
                raise RuntimeError("unable to get user def item")

            callable_def = type_def_item.get_child(attribute_name)
            if callable_def:
                # attribute already added
                self.items.append_use(user_def, callable_def)
            else:
                # add new attribute
                astroid_node = name_node.parent
                child = self.items.create_def(attribute_name, DefItemType.MEMBER, astroid_node)
                self.items.append_def_parent(type_def_item, child)
                self.items.append_use(user_def, child)
            return True

        # name_node - describes free function
        callable_def = self._get_callable_def(name_node)
        if callable_def is None:
            return False
        user_def = self.items.find_scope(name_node)
        if user_def is None:
            raise RuntimeError("unable to get user def item")
        self.items.append_use(user_def, callable_def)
        return True

    # get item defined by attribute
    def _resolve_attribute(self, attr_node: NodeNG):
        full_call = self._get_attr_full_call(attr_node)
        return self._resolve_item(attr_node, full_call)

    # ============================================

    def _get_attr_full_call(self, attr_node: NodeNG):
        if isinstance(attr_node, (node_classes.Name, node_classes.AssignName)):
            inferred = infer_type(attr_node)
            item_name = {"name": attr_node.name, "node": attr_node, "inferred": inferred}
            return [item_name]

        if isinstance(attr_node, node_classes.Attribute):
            inferred = infer_type(attr_node)
            sub_list = self._get_attr_full_call(attr_node.expr)
            item_attr = {"name": attr_node.attrname, "node": attr_node, "inferred": inferred}
            sub_list.append(item_attr)
            return sub_list

        if isinstance(attr_node, node_classes.AssignAttr):
            inferred = infer_type(attr_node)
            sub_list = self._get_attr_full_call(attr_node.expr)
            item_attr = {"name": attr_node.attrname, "node": attr_node, "inferred": inferred}
            sub_list.append(item_attr)
            return sub_list

        if isinstance(attr_node, node_classes.Call):
            inferred = infer_type(attr_node)
            sub_list = self._get_attr_full_call(attr_node.func)
            sub_list[-1]["inferred"] = inferred
            return sub_list

        if isinstance(attr_node, node_classes.Subscript):
            inferred = infer_type(attr_node)
            sub_list = self._get_attr_full_call(attr_node.value)
            sub_list[-1]["inferred"] = inferred
            return sub_list

        # msg = get_message("unhandled case", attr_node)
        # raise RuntimeError(msg)

        # ignore type
        return []

    def _resolve_item(self, attr_node: NodeNG, item_list) -> List[DefItem]:
        if not item_list:
            return []

        # first item can be function call
        first_item = item_list[0]
        first_name = first_item["name"]
        first_def: Optional[DefItem] = self._find_type_def_in_scope(attr_node, first_name)
        first_item["def"] = first_def
        first_item["type_def"] = None

        # ignore first item, because it is "self" or scope variable
        for idx in range(1, len(item_list)):
            item = item_list[idx]
            item["def"] = None
            item["type_def"] = None

            prev_item = item_list[idx - 1]

            prev_type: Optional[NodeNG] = prev_item["inferred"]
            prev_type_def = self.items.find_def_item(prev_type)
            if not prev_type_def:
                prev_type_def = prev_item.get("type_def")
            prev_item["type_def"] = prev_type_def

            if not prev_type_def:
                # item not found - seems like 'prev_type' is builtins type
                continue

            item_name = item["name"]
            item_def = prev_type_def.get_child(item_name)
            item["def"] = item_def
            if item_def:
                item["type_def"] = item_def.type_hint

        ret_list = []
        for item in item_list:
            ret_list.append(item.get("def"))
        return ret_list

    # 'func_name' is callable (function name or class name)
    def _get_callable_def(self, name_node: NodeNG) -> Optional[DefItem]:
        item_type: Optional[DefItem] = self._find_type_def(name_node, name_node.name)
        # func_name = name_node.name
        # item_type: Optional[DefItem] = self._get_type_item(func_name)
        if item_type is None:
            return None
        return self._get_callable(item_type)

    def _get_callable(self, item_type: DefItem):
        if item_type.type != DefItemType.CLASS:
            # calling function
            return item_type
        # calling constructor
        ctor_item = item_type.get_child("__init__")
        if ctor_item is not None:
            return ctor_item
        # constructor not explicitly defined - add node
        ctor_item = self.items.create_def("__init__", DefItemType.DEF_METHOD, None)
        self.items.append_def_parent(item_type, ctor_item)
        return ctor_item

    def _find_type_def(self, astroid_node: NodeNG, node_name: str = None) -> Optional[DefItem]:
        type_name = get_type(astroid_node)
        if type_name is None:
            type_name = node_name
        if type_name is None:
            return None
        return self._find_type_def_in_scope(astroid_node, type_name)

    def _find_type_def_in_scope(self, astroid_node: NodeNG, item_name: str = None) -> Optional[DefItem]:
        name_scope = astroid_node.scope()
        found_type_node: Optional[NodeNG] = self.items.find_in_scope(name_scope, item_name)
        if found_type_node is None:
            # happens for build-ins such as "print"
            return None

        found_def_item = self.items.find_def_item(found_type_node)
        if found_def_item is not None:
            return found_def_item

        # unable to find definition - seems "forward declaration" case (call before definition)
        # visit found node to generate definition
        self._visit(found_type_node)

        return self.items.find_def_item(found_type_node)


# ============================================


class TreeParser:
    def __init__(self):
        self.items = ItemContainer()

    def analyze(self, astroid_node: astroid_nodes.Module):
        self.items.add_mod(astroid_node)

        _LOGGER.info("=== analyzing astroid definitions ===")
        def_parser = DefParser(self.items)
        def_parser.analyze(astroid_node)

        _LOGGER.info("=== analyzing astroid usage ===")
        use_parser = UseParser(self.items)
        use_parser.analyze(astroid_node)

    def analyze_code(self, code, module_name=""):
        astroid_node = astroid.parse(code)
        astroid_node.name = module_name
        self.analyze(astroid_node)

    def analyze_files(self, files_list):
        root_paths = set()
        for src_file_path in files_list:
            pkg_root = get_package_root(src_file_path)
            root_paths.add(pkg_root)
        for pkg_root in root_paths:
            # fixes importing packages from Import and ImportFrom node
            sys.path.append(pkg_root)

        astroid_tree_list = []
        for src_file_path in files_list:
            astroid_tree: astroid_nodes.Module = astroid.MANAGER.ast_from_file(src_file_path)
            self.items.add_mod(astroid_tree)
            astroid_tree_list.append(astroid_tree)

        for astroid_tree in astroid_tree_list:
            _LOGGER.info("=== analyzing astroid definitions: %s", astroid_tree.file)
            def_parser = DefParser(self.items)
            def_parser.analyze(astroid_tree)

        for astroid_tree in astroid_tree_list:
            _LOGGER.info("=== analyzing astroid usage: %s", astroid_tree.file)
            use_parser = UseParser(self.items)
            use_parser.analyze(astroid_tree)


# ============================================


def get_modname(file_path):
    package_root = get_package_root(file_path)
    file_modname = get_file_modname(file_path)
    relative_path = os.path.relpath(file_modname, package_root)
    module_name = relative_path.replace("/", ".")
    module_name = module_name.replace("\\", ".")
    return module_name


def get_package_root(file_path):
    abs_path = os.path.abspath(file_path)
    prev_dirname = abs_path
    dir_name = prev_dirname
    while True:
        dir_name = os.path.dirname(dir_name)
        if dir_name == prev_dirname:
            # no __init__.py found in path directories
            break
        if not _has_init(dir_name):
            return dir_name
        prev_dirname = dir_name

    # no top package found
    return os.path.dirname(file_path)


# return file path without extension
def get_file_modname(file_path):
    dir_name = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    return os.path.join(dir_name, base_name)
