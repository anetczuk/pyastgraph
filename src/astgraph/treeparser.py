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
        self.def_items: List[DefItem] = []                  # list of all def items
        self.use_dict: Dict[DefItem, List[DefItem]] = {}
        self.astroid_item_dict: Dict[int, DefItem] = {}     # map astroid node (id) to def item
        self.astroid_node_dict: Dict[int, NodeNG] = {}

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


class TreeParser:

    def __init__(self):
        self.items = ItemContainer()
        self.astroid_module = None

    def analyze_code(self, code, module_name=""):
        astroid_node = astroid.parse(code)
        astroid_node.name = module_name
        self.analyze(astroid_node)

    def analyze(self, astroid_node):
        _LOGGER.info("=== analyzing astroid node ===")
        self._visit(astroid_node)

    # ============================================

    def visit_module(self, astroid_node):
        _LOGGER.debug("visiting Module %s", astroid_node.name)
        self.astroid_module = astroid_node
        mod_name = astroid_node.name
        mod_name = os.path.basename(mod_name)
        if mod_name.endswith(".py"):
            mod_name = mod_name[:-3]

        moduledef = self.items.create_def(mod_name, DefItemType.MODULE, astroid_node)
        moduledef.filename = astroid_node.file
        self.items.append_def(moduledef)

        self._visit_body(astroid_node)

    def visit_classdef(self, astroid_node):
        _LOGGER.debug("visiting ClassDef %s", astroid_node.name)
        if self.items.find_def_item(astroid_node):
            # already defined - happens in "forward declarations"
            _LOGGER.debug("%s already handled", astroid_node.name)
            return

        class_name = astroid_node.name
        classdef = self.items.create_def(class_name, DefItemType.CLASS, astroid_node)
        self.items.append_def(classdef)

        self._visit_body(astroid_node)

    def visit_functiondef(self, astroid_node):
        _LOGGER.debug("visiting FunctionDef %s", astroid_node.name)
        if self.items.find_def_item(astroid_node):
            # already defined - happens in "forward declarations"
            _LOGGER.debug("%s already handled", astroid_node.name)
            return

        func_name = astroid_node.name
        functiondef = self.items.create_def(func_name, DefItemType.MEMBER, astroid_node)
        self.items.append_def(functiondef)

        self._visit_body(astroid_node)

    def visit_assign(self, astroid_node):
        _LOGGER.debug("visiting Assign")
        if len(astroid_node.targets) != 1:
            raise RuntimeError("unsupported number of Assign targets")

        assign_val = astroid_node.value
        if isinstance(assign_val, node_classes.Call):
            _LOGGER.debug("unhandled Assign value %s in:\n%s", type(assign_val), astroid_node.repr_tree())
            if not self._handle_call(assign_val):
                call_func = assign_val.func
                _LOGGER.debug("unhandled Assign Call func %s in:\n%s", type(call_func), astroid_node.repr_tree())

        target = astroid_node.targets[0]

        if isinstance(target, node_classes.AssignAttr):
            # object attribute assignment
            return self._handle_attribute(target)

        if isinstance(target, node_classes.AssignName):
            # variable assignment
            curr_scope = self.items.find_scope(target)
            if curr_scope is None:
                raise RuntimeError("missing required current scope")
            if curr_scope.type != DefItemType.CLASS:
                # assigning local variable
                return

            # assigning class variable (static field)
            assign_name = target.name
            child = curr_scope.get_child(assign_name)
            if child is None:
                child = self.items.create_def(assign_name, DefItemType.MEMBER, astroid_node)
                self.items.append_def(child)
            # class scope definitions - do not add to uses
            # self.items.append_use(child)
            return

        raise RuntimeError(f"unknown Assign target: {type(target)}")

    def visit_expr(self, astroid_node):
        _LOGGER.debug("visiting Expr")
        expr_value = astroid_node.value
        if not isinstance(expr_value, node_classes.Call):
            raise RuntimeError("missing required Call node")
        if not self._handle_call(expr_value):
            call_func = expr_value.func
            _LOGGER.debug("unhandled Expr Call func %s in:\n%s", type(call_func), astroid_node.repr_tree())
            return

    def visit_if(self, astroid_node):
        _LOGGER.debug("visiting If")
        self._visit_body(astroid_node)

    def visit_return(self, astroid_node):
        _LOGGER.debug("visiting Return")
        ret_val = astroid_node.value
        if not self._handle_call(ret_val):
            _LOGGER.debug("unhandled Return value in:\n%s", astroid_node.repr_tree())

    def _visit(self, astroid_node):
        if isinstance(astroid_node, astroid_nodes.Module):
            self.visit_module(astroid_node)
            return
        if isinstance(astroid_node, astroid_nodes.ClassDef):
            self.visit_classdef(astroid_node)
            return
        if isinstance(astroid_node, astroid_nodes.FunctionDef):
            self.visit_functiondef(astroid_node)
            return
        if isinstance(astroid_node, node_classes.Assign):
            self.visit_assign(astroid_node)
            return
        if isinstance(astroid_node, node_classes.Expr):
            self.visit_expr(astroid_node)
            return
        if isinstance(astroid_node, node_classes.If):
            self.visit_if(astroid_node)
            return
        if isinstance(astroid_node, node_classes.Return):
            self.visit_return(astroid_node)
            return
        if isinstance(astroid_node, node_classes.Pass):
            # do nothing
            return

        repr_tree = astroid_node.repr_tree()
        _LOGGER.warning("unahndled node:\n%s", repr_tree)
        raise RuntimeError(f"unhandled node: {type(astroid_node)}")

    def _visit_body(self, astroid_node):
        for item_node in astroid_node.body:
            self._visit(item_node)

    # ============================================

    def _handle_call(self, call_node) -> bool:
        # handle function arguments
        for arg_node in call_node.args:
            if isinstance(arg_node, node_classes.Attribute):
                # call of object's method (self or variable)
                self._handle_attribute(arg_node)
            else:
                _LOGGER.warning("unhandled Call arg type %s in:\n%s", type(arg_node), call_node.parent.repr_tree())

        # handle function
        call_func = call_node.func

        if isinstance(call_func, node_classes.Attribute):
            # call of object's method (self or variable)
            return self._handle_attribute(call_func)

        if isinstance(call_func, node_classes.Name):
            # call of free function
            return self._handle_name(call_func, None)

            # func_name = call_func.name
            # return self._handle_type_use(func_name)

        return False

    def _handle_attribute(self, arg_node) -> bool:
        func_expr = arg_node.expr

        if isinstance(func_expr, node_classes.Name):
            func_attrname = arg_node.attrname
            return self._handle_name(func_expr, func_attrname)

        if isinstance(func_expr, node_classes.Attribute):
            # chained call, e.g.: self.value_dict.get("xxx")
            expr_type = get_type(func_expr)
            if expr_type is not None:
                expr_attrname = arg_node.attrname

                item_type: Optional[DefItem] = self._get_type_item(expr_type)
                if item_type is None:
                    _LOGGER.warning("unable to find attribute item of type %s", expr_type)
                    return self._handle_attribute(func_expr)
                if item_type.type != DefItemType.CLASS:
                    _LOGGER.warning("unable to handle Attribute type")
                    return self._handle_attribute(func_expr)
    
                item_member = item_type.get_child(expr_attrname)
                if item_member is None:
                    _LOGGER.warning("unable to handle Attribute - missing member %s", expr_attrname)
                    return self._handle_attribute(func_expr)

                user_def = self.items.find_scope(arg_node)
                if not user_def:
                    raise RuntimeError("unable to get user def item")

                self.items.append_use(user_def, item_member)
                return self._handle_attribute(func_expr)

        raise RuntimeError(f"missing required Name node, got: {type(func_expr)}")

    # if given then 'attribute_name' is name of member of object defined by 'name_node'
    # if 'attribute_name' is empty, then 'name_node' is name of free function
    def _handle_name(self, name_node: NodeNG, attribute_name: Optional[str]) -> bool:
        if attribute_name:
            # name_node - describes object
            # attribute_name - describes object's member
            type_def_item: Optional[DefItem] = self._find_type_def(name_node)
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
            func_name = name_node.name
            callable_def = self._get_callable_def(func_name)
            if callable_def is None:
                return False

            user_def = self.items.find_scope(name_node)
            if user_def is None:
                raise RuntimeError("unable to get user def item")

            self.items.append_use(user_def, callable_def)
            return True

    # ============================================

    # 'func_name' is callable (function name or class name)
    def _get_callable_def(self, func_name: str) -> Optional[DefItem]:
        item_type = self._get_type_item(func_name)
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

    def _find_type_def(self, name_node: NodeNG) -> Optional[DefItem]:
        variable_type = get_type(name_node)
        if variable_type:
            return self._get_type_item(variable_type)
        type_name = name_node.name
        return self._get_type_item(type_name)

    def _get_type_item(self, type_name: str) -> Optional[DefItem]:
        if self.astroid_module is None:
            raise RuntimeError("missing module")
        found_type_node = self.astroid_module.locals.get(type_name)
        if found_type_node is None:
            found_type_node = self.astroid_module.globals.get(type_name)

        if found_type_node is None:
            # happens for build-ins such as "print"
            return None

        if len(found_type_node) != 1:
            raise RuntimeError("unsupported number of definitions")

        found_type_node = found_type_node[0]
        
        found_def_item = self.items.find_def_item(found_type_node)
        if found_def_item is not None:
            return found_def_item

        # unable to find definition - seems "forward declaration" case (call before definition)
        # visit found node to generate definition
        self._visit(found_type_node)

        return self.items.find_def_item(found_type_node)
