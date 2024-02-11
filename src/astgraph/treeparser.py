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
from typing import List, Any, Optional

import astroid.nodes.scoped_nodes.scoped_nodes as astroid_nodes
from astroid.nodes import node_classes

import astypes


_LOGGER = logging.getLogger(__name__)


# ============================================


class DefItemType(Enum):
    MODULE = "module"
    CLASS = "class"
    MEMBER = "member"  # free function, method or attribute


class DefItem:
    def __init__(self, name: str, item_type: DefItemType, astroid_node, namespace=""):
        self.node_id = id(astroid_node)
        self.type: DefItemType = item_type
        self.parent = None
        self.namespace = namespace
        self.name = name
        self.filename = None
        self.items: List[Any] = []

    def append(self, item):
        item.namespace = self.get_full_name()
        self.items.append(item)
        item.parent = self

    def get_namespace(self):
        return self.namespace

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
        if self.filename:
            return self.filename
        if self.parent:
            return self.parent.get_filename()
        return None

    def get_child(self, name):
        for item in self.items:
            if item.name == name:
                return item
        return None


# ============================================


class TreeParser:
    def __init__(self):
        self.def_items = []  # list of all def items
        self.def_scope = []  # def stack
        self.use_dict = {}

        self.astroid_item_dict = {}     # map astroid node (id) to def item
        self.astroid_module = None

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

        moduledef = self._create_def(mod_name, DefItemType.MODULE, astroid_node)
        moduledef.filename = astroid_node.file

        self._append_def(moduledef)

        self.def_scope.append(moduledef)
        self._visit_body(astroid_node)
        self.def_scope.pop()

    def visit_classdef(self, astroid_node):
        _LOGGER.debug("visiting ClassDef %s", astroid_node.name)
        class_name = astroid_node.name
        classdef = self._get_def_child(class_name)
        if classdef is None:
            classdef = self._create_def(class_name, DefItemType.CLASS, astroid_node)
            self._append_def(classdef)

        self.def_scope.append(classdef)
        self._visit_body(astroid_node)
        self.def_scope.pop()

    def visit_functiondef(self, astroid_node):
        _LOGGER.debug("visiting FunctionDef %s", astroid_node.name)
        func_name = astroid_node.name
        functiondef = self._get_def_child(func_name)
        if functiondef is None:
            functiondef = self._create_def(func_name, DefItemType.MEMBER, astroid_node)
            self._append_def(functiondef)

        self.def_scope.append(functiondef)
        self._visit_body(astroid_node)
        self.def_scope.pop()

    def visit_assign(self, astroid_node):
        _LOGGER.debug("visiting Assign")
        if len(astroid_node.targets) != 1:
            raise RuntimeError("unsupported number of Assign targets")
        target = astroid_node.targets[0]
        if isinstance(target, node_classes.AssignAttr):
            # assigning attribute
            target_attrname = target.attrname
            target_expr = target.expr
            if not isinstance(target_expr, node_classes.Name):
                raise RuntimeError("missing required Name node")
            target_scope = target_expr.name
            if target_scope != "self":
                # assigning attribute on local variable
                return
    
            parent_class = self._get_parent_class()
            if parent_class is None:
                raise RuntimeError("missing required class scope")
            child = parent_class.get_child(target_attrname)
            if child is None:
                child = self._create_def(target_attrname, DefItemType.MEMBER, astroid_node)
                self._append_def_parent(parent_class, child)
            self._append_use(child)
            return

        if isinstance(target, node_classes.AssignName):
            curr_scope = self._get_curr_scope()
            if curr_scope is None:
                raise RuntimeError("missing required current scope")
            if curr_scope.type != DefItemType.CLASS:
                # assigning local variable
                assign_val = astroid_node.value
                if not isinstance(assign_val, node_classes.Call):
                    _LOGGER.debug("unhandled Assign value %s in:\n%s", type(assign_val), astroid_node.repr_tree())
                    return
                if not self._handle_call(assign_val):
                    call_func = assign_val.func
                    _LOGGER.debug("unhandled Assign Call func %s in:\n%s", type(call_func), astroid_node.repr_tree())
                return

            assign_name = target.name
            child = curr_scope.get_child(assign_name)
            if child is None:
                child = self._create_def(assign_name, DefItemType.MEMBER, astroid_node)
                self._append_def(child)
            # class scope definitions - do not add to uses
            # self._append_use(child)
            return

        raise RuntimeError(f"unknown Assign target: {type(target)}")

    def visit_expr(self, astroid_node):
        _LOGGER.debug("visiting Expr")
        if not self.def_scope:
            raise RuntimeError("missing scope")
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

    # ============================================

    def _get_curr_scope(self):
        if not self.def_scope:
            return None
        return self.def_scope[-1]

    def _get_def_child(self, child_name):
        parent_def = self.def_scope[-1]
        if parent_def is None:
            raise RuntimeError("missing required parent scope")
        return parent_def.get_child(child_name)

    # return parent of type module or class
    def _get_parent_class(self):
        parent_def = self.def_scope[-1]
        if parent_def is None:
            raise RuntimeError("missing required parent scope")

        while parent_def:
            if parent_def.type == DefItemType.CLASS:
                return parent_def
            parent_def = parent_def.parent

        return None

    def _get_constructor(self, class_item):
        constr_item = class_item.get_child("__init__")
        if constr_item is not None:
            return constr_item
        # constructor not explicitly defined - add node
        constr_item = self._create_def("__init__", DefItemType.MEMBER, None)
        class_item.append(constr_item)
        return constr_item

    def _find_type_item(self, type_name) -> Optional[DefItem]:
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
        found_id = id(found_type_node)
        return self.astroid_item_dict.get(found_id)

    def _handle_call(self, call_node) -> bool:
        call_args = call_node.args
        for arg_node in call_args:
            if isinstance(arg_node, node_classes.Attribute):
                # call of object's method (self or variable)
                self._handle_arg(arg_node)
            else:
                _LOGGER.warning("unhandled Call arg type %s", type(arg_node))

        call_func = call_node.func
        if isinstance(call_func, node_classes.Name):
            # call of free function
            func_name = call_func.name
            return self._handle_type_use(func_name)

        if isinstance(call_func, node_classes.Attribute):
            # call of object's method (self or variable)
            return self._handle_arg(call_func)

        return False

    def _handle_arg(self, arg_node) -> bool:
        func_attrname = arg_node.attrname
        func_expr = arg_node.expr
        if not isinstance(func_expr, node_classes.Name):
            raise RuntimeError("missing required Name node")

        func_scope = func_expr.name
        if func_scope == "self":
            parent_class = self._get_parent_class()
            if parent_class is None:
                raise RuntimeError("missing required class scope")
            child = parent_class.get_child(func_attrname)
            if child is None:
                child = self._create_def(func_attrname, DefItemType.MEMBER, arg_node)
                self._append_def_parent(parent_class, child)
            self._append_use(child)
            return True

        # running method on local object
        node_astype = astypes.get_type(func_expr)
        if not node_astype:
            _LOGGER.warning("unable to handle Attribute node - unknown expression type")
            return False
        variable_type = node_astype.annotation
        item_type = self._find_type_item(variable_type)
        if item_type is None:
            _LOGGER.warning("unable to find type: %s", item_type)
            return False
        if item_type.type != DefItemType.CLASS:
            _LOGGER.warning("unable to handle Attribute type")
            return False

        item_member = item_type.get_child(func_attrname)
        if item_member is None:
            _LOGGER.warning("unable to handle Attribute - missing member %s")
            return False
        self._append_use(item_member)
        return True

    def _handle_type_use(self, type_name) -> bool:
        item_type = self._find_type_item(type_name)
        if item_type is None:
            return False
        if item_type.type == DefItemType.CLASS:
            # calling constructor
            constructor_item = self._get_constructor(item_type)
            self._append_use(constructor_item)
        else:
            # calling function
            self._append_use(item_type)
        return True

    def _create_def(self, name, def_type, astroid_node):
        item = DefItem(name, def_type, astroid_node)
        if astroid_node is not None:
            node_id = id(astroid_node)
            self.astroid_item_dict[node_id] = item
        return item

    def _append_def(self, def_item):
        self.def_items.append(def_item)
        if not self.def_scope:
            _LOGGER.debug("append def: %s", def_item.name)
            return
        parent = self.def_scope[-1]
        parent.append(def_item)
        _LOGGER.debug("append def: %s -> %s", parent.name, def_item.name)

    def _append_def_parent(self, parent, def_item):
        _LOGGER.debug("append def: %s -> %s", parent.name, def_item.name)
        self.def_items.append(def_item)
        parent.append(def_item)

    def _append_use(self, use_item):
        # here we are sure that 'use_item' is already added to def structures
        if not self.def_scope:
            return
        parent_def = self.def_scope[-1]
        uses_list = self.use_dict.get(parent_def)
        if uses_list is None:
            uses_list = []
            self.use_dict[parent_def] = uses_list
        if use_item not in uses_list:
            _LOGGER.debug("append use: %s -> %s", parent_def.name, use_item.name)
            uses_list.append(use_item)

    def _visit_body(self, astroid_node):
        for item_node in astroid_node.body:
            self._visit(item_node)

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

        repr_tree = astroid_node.repr_tree()
        _LOGGER.warning("unahndled node:\n%s", repr_tree)
        raise RuntimeError(f"unhandled node: {type(astroid_node)}")
