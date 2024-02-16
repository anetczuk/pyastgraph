#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import os
import logging
from enum import Enum
from typing import Dict, List, Any, Optional

import astroid
import astroid.nodes.scoped_nodes.scoped_nodes as astroid_nodes
from astroid.nodes import node_classes, NodeNG

import astypes


_LOGGER = logging.getLogger(__name__)


# ============================================


class DefItemType(Enum):
    MODULE = "module"
    CLASS = "class"
    MEMBER = "member"  # free function, method or attribute


class DefItem:
    def __init__(self, name: str, item_type: DefItemType, astroid_node):
        self.node_id = id(astroid_node)
        self.type: DefItemType = item_type
        self.parent = None
        self.name = name
        self.items: List[Any] = []

    @property
    def info(self):
        return (self.get_full_name(), self.type)

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


def get_type(type_name: NodeNG) -> str:
    node_astype = astypes.get_type(type_name)
    if not node_astype:
        return None
    return node_astype.annotation


# ============================================


class ItemContainer:
    def __init__(self):
        self.def_items: List[DefItem] = []  # list of all def items
        self.use_dict: Dict[DefItem, List[DefItem]] = {}
        self.astroid_item_dict: Dict[int, DefItem] = {}  # map astroid node (id) to def item
        self.astroid_node_dict: Dict[int, NodeNG] = {}

    def get_def_list(self):
        ret_list = []
        for def_item in self.def_items:
            ret_list.append(def_item.info)
        return ret_list

    def get_use_list(self):
        ret_list = []
        for def_key, def_list in self.use_dict.items():
            for def_item in def_list:
                ret_list.append((def_key.get_full_name(), def_item.get_full_name()))
        return ret_list

    def create_def(self, name: str, def_type: DefItemType, astroid_node: NodeNG):
        if def_type == DefItemType.MODULE:
            item = ModuleItem(name, astroid_node)
        else:
            item = DefItem(name, def_type, astroid_node)
        if astroid_node is not None:
            node_id = id(astroid_node)
            self.astroid_item_dict[node_id] = item
            self.astroid_node_dict[node_id] = astroid_node
        return item

    def append_def(self, def_item: DefItem):
        if not self.def_items:
            # empty list - first item
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

    def get_parent_scope(self, astroid_node: NodeNG) -> Optional[DefItem]:
        parent_node = astroid_node.parent  # scope returns self
        if parent_node is None:
            # no parent scope
            return None
        scope_node = parent_node.scope()
        return self.find_def_item(scope_node)

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


# ============================================


class DefParser:
    def __init__(self, container: ItemContainer = None):
        if container is None:
            container = ItemContainer()
        self.items = container
        self.astroid_tree = None

    def analyze(self, astroid_node):
        _LOGGER.info("=== analyzing astroid node definitions ===")
        self.astroid_tree = astroid_node
        self._visit(astroid_node)

    # ============================================================

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

        moduledef = self.items.create_def(mod_name, DefItemType.MODULE, astroid_node)
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
        functiondef = self.items.create_def(func_name, DefItemType.MEMBER, astroid_node)
        self.items.append_def(functiondef)

        self._visit_children(astroid_node)


# ============================================


class TreeParser:
    def __init__(self):
        self.items = ItemContainer()
        self.astroid_tree = None

    def analyze_code(self, code, module_name=""):
        astroid_node = astroid.parse(code)
        astroid_node.name = module_name
        self.analyze(astroid_node)

    def analyze(self, astroid_node):
        self.astroid_tree = astroid_node
        def_parser = DefParser(self.items)
        def_parser.analyze(astroid_node)
        _LOGGER.info("=== analyzing astroid node ===")
        self._visit(astroid_node)

    # ============================================

    def _visit(self, astroid_node):
        _LOGGER.debug("visiting item: %s", type(astroid_node))

        if isinstance(astroid_node, node_classes.Call):
            self.visit_call(astroid_node)
            return
        if isinstance(astroid_node, node_classes.AssignName):
            self.visit_assignname(astroid_node)
            return
        if isinstance(astroid_node, node_classes.AssignAttr):
            self.visit_assignattr(astroid_node)
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

        # handle function
        call_func = astroid_node.func
        if isinstance(call_func, node_classes.Name):
            # call of free function
            self._handle_name(call_func, None)

        self._visit_children(astroid_node)

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

    def visit_attribute(self, astroid_node):
        # read value from object's attribute
        _LOGGER.debug("visiting Attribute")

        attr_expr = astroid_node.expr
        if isinstance(attr_expr, node_classes.Name):
            attr_name = astroid_node.attrname
            self._handle_name(attr_expr, attr_name)
            return

        if isinstance(attr_expr, node_classes.Attribute):
            attr_name = astroid_node.attrname
            type_def_item: Optional[DefItem] = self._find_type_def(attr_expr, attr_name)
            if type_def_item:
                if type_def_item.type != DefItemType.CLASS:
                    _LOGGER.warning("unable to handle Attribute type")
                    return False

                user_def = self.items.get_parent_scope(astroid_node)
                if not user_def:
                    raise RuntimeError("unable to get user def item")

                callable_def = type_def_item.get_child(attr_name)
                if callable_def:
                    # attribute already added
                    self.items.append_use(user_def, callable_def)
                else:
                    # add new attribute
                    child = self.items.create_def(attr_name, DefItemType.MEMBER, astroid_node)
                    self.items.append_def_parent(type_def_item, child)
                    self.items.append_use(user_def, child)

        self._visit_children(astroid_node)

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

        else:
            # name_node - describes free function
            callable_def = self._get_callable_def(name_node)
            if callable_def is None:
                return False
            user_def = self.items.find_scope(name_node)
            if user_def is None:
                raise RuntimeError("unable to get user def item")
            self.items.append_use(user_def, callable_def)
            return True

    # ============================================

    # 'func_name' is callable (function name or class name)
    def _get_callable_def(self, name_node: NodeNG) -> Optional[DefItem]:
        item_type: Optional[DefItem] = self._find_type_def(name_node, name_node.name)
        # func_name = name_node.name
        # item_type: Optional[DefItem] = self._get_type_item(func_name)
        if item_type is None:
            return None
        if item_type.type != DefItemType.CLASS:
            # calling function
            return item_type

        # calling constructor
        constr_item = item_type.get_child("__init__")
        if constr_item is not None:
            return constr_item
        # constructor not explicitly defined - add node
        constr_item = self.items.create_def("__init__", DefItemType.MEMBER, None)
        item_type.append(constr_item)
        return constr_item

    def _find_type_def(self, astroid_node: NodeNG, node_name: str) -> Optional[DefItem]:
        type_name = get_type(astroid_node)
        if type_name is None:
            type_name = node_name
        if type_name is None:
            return None
        name_scope = astroid_node.scope()
        found_type_node = self._find_in_scope(name_scope, type_name)
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

    # name is type name or variable name
    def _find_in_scope(self, scope_node, name) -> Optional[NodeNG]:
        while scope_node:
            found_type_node = scope_node.locals.get(name)
            if found_type_node:
                # found node
                return found_type_node[0]
            parent_node = scope_node.parent  # scope returns self
            if parent_node is None:
                # no parent scope
                return None
            scope_node = parent_node.scope()
        return None
