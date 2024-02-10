#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import os

from enum import Enum
from typing import List, Any

import astroid.nodes.scoped_nodes.scoped_nodes as astroid_nodes
from astroid.nodes import node_classes


class TreeParser:
    def __init__(self):
        self.def_items = []  # list of all def items
        self.def_scope = []  # def stack
        self.use_dict = {}

    def analyze(self, tree):
        self._visit(tree)

    # ============================================

    def visit_module(self, astroid_node):
        mod_name = astroid_node.name
        mod_name = os.path.basename(mod_name)
        if mod_name.endswith(".py"):
            mod_name = mod_name[:-3]

        moduledef = DefItem(mod_name, DefItemType.MODULE)
        moduledef.filename = astroid_node.file

        self._append_def(moduledef)

        self.def_scope.append(moduledef)
        self._visit_body(astroid_node)
        self.def_scope.pop()

    def visit_classdef(self, astroid_node):
        class_name = astroid_node.name
        classdef = self._get_def_child(class_name)
        if classdef is None:
            classdef = DefItem(class_name, DefItemType.CLASS)
            self._append_def(classdef)

        self.def_scope.append(classdef)
        self._visit_body(astroid_node)
        self.def_scope.pop()

    def visit_functiondef(self, astroid_node):
        func_name = astroid_node.name
        functiondef = self._get_def_child(func_name)
        if functiondef is None:
            functiondef = DefItem(func_name, DefItemType.MEMBER)
            self._append_def(functiondef)

        self.def_scope.append(functiondef)
        self._visit_body(astroid_node)
        self.def_scope.pop()

    def visit_assign(self, astroid_node):
        if len(astroid_node.targets) != 1:
            raise RuntimeError("unsupported number of Assign targets")
        target = astroid_node.targets[0]
        if not isinstance(target, node_classes.AssignAttr):
            raise RuntimeError("missing required AssignAttr node")

        target_attrname = target.attrname
        target_expr = target.expr
        if not isinstance(target_expr, node_classes.Name):
            raise RuntimeError("missing required Name node")
        target_scope = target_expr.name
        if target_scope != "self":
            raise RuntimeError("missing required self scope")

        parent_class = self._get_parent_class()
        if parent_class is None:
            raise RuntimeError("missing required class scope")
        child = parent_class.get_child(target_attrname)
        if child is None:
            child = DefItem(target_attrname, DefItemType.MEMBER)
            self._append_def_parent(parent_class, child)
        self._append_use(child)

    def visit_expr(self, astroid_node):
        if not self.def_scope:
            raise RuntimeError("missing scope")
        expr_value = astroid_node.value
        if not isinstance(expr_value, node_classes.Call):
            raise RuntimeError("missing required Call node")
        expr_func = expr_value.func
        if not isinstance(expr_func, node_classes.Attribute):
            raise RuntimeError("missing required Attribute node")

        func_attrname = expr_func.attrname
        func_expr = expr_func.expr
        if not isinstance(func_expr, node_classes.Name):
            raise RuntimeError("missing required Name node")
        func_scope = func_expr.name
        if func_scope != "self":
            raise RuntimeError("missing required self scope")

        parent_class = self._get_parent_class()
        if parent_class is None:
            raise RuntimeError("missing required class scope")
        child = parent_class.get_child(func_attrname)
        if child is None:
            child = DefItem(func_attrname, DefItemType.MEMBER)
            self._append_def_parent(parent_class, child)
        self._append_use(child)

    # ============================================

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

        raise RuntimeError("missing required parent class")

    def _append_def(self, def_item):
        self.def_items.append(def_item)
        if not self.def_scope:
            return
        parent = self.def_scope[-1]
        parent.append(def_item)

    def _append_def_parent(self, parent, def_item):
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

        raise RuntimeError(f"unhandled node: {type(astroid_node)}")


# ============================================


class DefItemType(Enum):
    MODULE = "module"
    CLASS = "class"
    MEMBER = "member"  # free function, method or attribute


class DefItem:
    def __init__(self, name: str, item_type: DefItemType, namespace=""):
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
