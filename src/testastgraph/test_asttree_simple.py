#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import unittest

from astgraph.pyanwrap import draw_full_graph
from astgraph.treeparser import TreeParser, DefItemType


def draw(parser, svg_out_path="/tmp/graph.svg"):
    output_dict = {"outsvgfile": svg_out_path}
    draw_full_graph(parser.items.def_items, parser.items.use_dict, output_dict)


def print_ast(parser):
    for astroid_mod in parser.items.mod_dict.values():
        ast_tree = astroid_mod.repr_tree()
        print(f"AST tree:\n{ast_tree}")


class TreeParserSimpleTest(unittest.TestCase):
    def test_analyze_variable(self):
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code="aaa = 5")

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 1)
        self.assertEqual(len(items_container.use_dict), 0)

        item = items_container.def_items[0]
        self.assertEqual(item.name, "testmod")
        self.assertEqual(item.get_namespace(), "")
        self.assertEqual(item.type, DefItemType.MODULE)

    def test_analyze_func(self):
        code = """\
def func():
    pass
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 2)
        self.assertEqual(len(items_container.use_dict), 0)

        self.assertEqual(items_container.def_items[0].type, DefItemType.MODULE)

        item = items_container.def_items[1]
        self.assertEqual(item.name, "func")
        self.assertEqual(item.get_namespace(), "testmod")
        self.assertEqual(item.type, DefItemType.DEF_METHOD)

    def test_analyze_func_call(self):
        code = """\
def func():
    pass

func()
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 2)
        self.assertEqual(len(items_container.use_dict), 1)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        item = items_container.def_items[1]
        self.assertEqual(item.name, "func")
        self.assertEqual(item.get_namespace(), "testmod")
        self.assertEqual(item.type, DefItemType.DEF_METHOD)

        mod_uses = items_container.use_dict[mod_item]
        self.assertEqual(len(mod_uses), 1)
        self.assertEqual(mod_uses[0].name, "func")
        self.assertEqual(mod_uses[0].type, DefItemType.DEF_METHOD)

    def test_analyze_func_call_02(self):
        code = """\
def func_a():
    pass

def func_b():
    func_a()
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 3)
        self.assertEqual(len(items_container.use_dict), 1)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        func_a_item = items_container.def_items[1]
        self.assertEqual(func_a_item.name, "func_a")
        self.assertEqual(func_a_item.get_namespace(), "testmod")
        self.assertEqual(func_a_item.type, DefItemType.DEF_METHOD)

        func_b_item = items_container.def_items[2]
        self.assertEqual(func_b_item.name, "func_b")
        self.assertEqual(func_b_item.get_namespace(), "testmod")
        self.assertEqual(func_b_item.type, DefItemType.DEF_METHOD)

        self.assertNotIn(mod_item, items_container.use_dict)
        self.assertNotIn(func_a_item, items_container.use_dict)
        self.assertIn(func_b_item, items_container.use_dict)

        faunc_b_uses = items_container.use_dict[func_b_item]
        self.assertEqual(len(faunc_b_uses), 1)
        self.assertEqual(faunc_b_uses[0], func_a_item)

    def test_analyze_func_call_02_forward(self):
        # parse code with function declared after it's use

        code = """\
def func_a():
    func_b()

def func_b():
    pass
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 3)
        self.assertEqual(len(items_container.use_dict), 1)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        func_a_item = items_container.def_items[1]
        self.assertEqual(func_a_item.name, "func_a")
        self.assertEqual(func_a_item.get_namespace(), "testmod")
        self.assertEqual(func_a_item.type, DefItemType.DEF_METHOD)

        func_b_item = items_container.def_items[2]
        self.assertEqual(func_b_item.name, "func_b")
        self.assertEqual(func_b_item.get_namespace(), "testmod")
        self.assertEqual(func_b_item.type, DefItemType.DEF_METHOD)

        self.assertNotIn(mod_item, items_container.use_dict)
        self.assertIn(func_a_item, items_container.use_dict)
        self.assertNotIn(func_b_item, items_container.use_dict)

        func_a_uses = items_container.use_dict[func_a_item]
        self.assertEqual(len(func_a_uses), 1)
        self.assertEqual(func_a_uses[0].name, "func_b")
        self.assertEqual(func_a_uses[0].type, DefItemType.DEF_METHOD)

    def test_analyze_func_param(self):
        code = """\
def func_a():
    return None

def func_b():
    print( func_a() )
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 3)
        self.assertEqual(len(items_container.use_dict), 1)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        func_a_item = items_container.def_items[1]
        self.assertEqual(func_a_item.name, "func_a")
        self.assertEqual(func_a_item.get_namespace(), "testmod")
        self.assertEqual(func_a_item.type, DefItemType.DEF_METHOD)

        func_b_item = items_container.def_items[2]
        self.assertEqual(func_b_item.name, "func_b")
        self.assertEqual(func_b_item.get_namespace(), "testmod")
        self.assertEqual(func_b_item.type, DefItemType.DEF_METHOD)

        self.assertNotIn(mod_item, items_container.use_dict)
        self.assertNotIn(func_a_item, items_container.use_dict)
        self.assertIn(func_b_item, items_container.use_dict)

        func_b_uses = items_container.use_dict[func_b_item]
        self.assertEqual(len(func_b_uses), 1)
        self.assertEqual(func_b_uses[0].name, "func_a")
        self.assertEqual(func_b_uses[0].type, DefItemType.DEF_METHOD)

    def test_analyze_func_assign(self):
        code = """\
def func_a():
    return None

xxx = func_a()
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 2)
        self.assertEqual(len(items_container.use_dict), 1)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        func_a_item = items_container.def_items[1]
        self.assertEqual(func_a_item.name, "func_a")
        self.assertEqual(func_a_item.get_namespace(), "testmod")
        self.assertEqual(func_a_item.type, DefItemType.DEF_METHOD)

        self.assertIn(mod_item, items_container.use_dict)

        mod_uses = items_container.use_dict[mod_item]
        self.assertEqual(len(mod_uses), 1)
        self.assertEqual(mod_uses[0].name, "func_a")
        self.assertEqual(mod_uses[0].type, DefItemType.DEF_METHOD)

    def test_analyze_func_call_recursive(self):
        code = """\
def func_a():
    func_a()
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 2)
        self.assertEqual(len(items_container.use_dict), 1)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        func_a_item = items_container.def_items[1]
        self.assertEqual(func_a_item.name, "func_a")
        self.assertEqual(func_a_item.get_namespace(), "testmod")
        self.assertEqual(func_a_item.type, DefItemType.DEF_METHOD)

        self.assertNotIn(mod_item, items_container.use_dict)
        self.assertIn(func_a_item, items_container.use_dict)

        func_a_uses = items_container.use_dict[func_a_item]
        self.assertEqual(len(func_a_uses), 1)
        self.assertEqual(func_a_uses[0].name, "func_a")
        self.assertEqual(func_a_uses[0].type, DefItemType.DEF_METHOD)

    def test_analyze_classdef(self):
        code = """\
class ABC:
    def __init__(self):
        pass
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 3)
        self.assertEqual(len(items_container.use_dict), 0)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        abc_item = items_container.def_items[1]
        self.assertEqual(abc_item.name, "ABC")
        self.assertEqual(abc_item.get_namespace(), "testmod")
        self.assertEqual(abc_item.type, DefItemType.CLASS)

        ctor_item = items_container.def_items[2]
        self.assertEqual(ctor_item.name, "__init__")
        self.assertEqual(ctor_item.get_namespace(), "testmod.ABC")
        self.assertEqual(ctor_item.type, DefItemType.DEF_METHOD)

    def test_analyze_field_assignattr(self):
        code = """\
class ABC:
    def __init__(self):
        self.data_field = 'xxx'
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 4)
        self.assertEqual(len(items_container.use_dict), 1)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        abc_item = items_container.def_items[1]
        self.assertEqual(abc_item.name, "ABC")
        self.assertEqual(abc_item.get_namespace(), "testmod")
        self.assertEqual(abc_item.type, DefItemType.CLASS)

        ctor_item = items_container.def_items[2]
        self.assertEqual(ctor_item.name, "__init__")
        self.assertEqual(ctor_item.get_namespace(), "testmod.ABC")
        self.assertEqual(ctor_item.type, DefItemType.DEF_METHOD)

        field_item = items_container.def_items[3]
        self.assertEqual(field_item.name, "data_field")
        self.assertEqual(field_item.get_namespace(), "testmod.ABC")
        self.assertEqual(field_item.type, DefItemType.MEMBER)

        self.assertIn(ctor_item, items_container.use_dict)

        ctor_uses = items_container.use_dict[ctor_item]
        self.assertEqual(len(ctor_uses), 1)
        self.assertEqual(ctor_uses[0].name, "data_field")
        self.assertEqual(ctor_uses[0].type, DefItemType.MEMBER)

    def test_analyze_call_self_method(self):
        code = """\
class ABC:
    def __init__(self):
        self.execute()

    def execute(self):
        print("executing")
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 4)
        self.assertEqual(len(items_container.use_dict), 1)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        abc_item = items_container.def_items[1]
        self.assertEqual(abc_item.name, "ABC")
        self.assertEqual(abc_item.get_namespace(), "testmod")
        self.assertEqual(abc_item.type, DefItemType.CLASS)

        ctor_item = items_container.def_items[2]
        self.assertEqual(ctor_item.name, "__init__")
        self.assertEqual(ctor_item.get_namespace(), "testmod.ABC")
        self.assertEqual(ctor_item.type, DefItemType.DEF_METHOD)

        field_item = items_container.def_items[3]
        self.assertEqual(field_item.name, "execute")
        self.assertEqual(field_item.get_namespace(), "testmod.ABC")
        self.assertEqual(field_item.type, DefItemType.DEF_METHOD)

        self.assertIn(ctor_item, items_container.use_dict)

        ctor_uses = items_container.use_dict[ctor_item]
        self.assertEqual(len(ctor_uses), 1)
        self.assertEqual(ctor_uses[0].name, "execute")
        self.assertEqual(ctor_uses[0].type, DefItemType.DEF_METHOD)

    def test_analyze_access_static(self):
        code = """\
class ABC:
    STATIC_FIELD = "initial_value"

def main():
    ABC.STATIC_FIELD = "main_value"
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 4)
        self.assertEqual(len(items_container.use_dict), 1)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        abc_item = items_container.def_items[1]
        self.assertEqual(abc_item.name, "ABC")
        self.assertEqual(abc_item.get_namespace(), "testmod")
        self.assertEqual(abc_item.type, DefItemType.CLASS)

        main_item = items_container.def_items[2]
        self.assertEqual(main_item.name, "main")
        self.assertEqual(main_item.get_namespace(), "testmod")
        self.assertEqual(main_item.type, DefItemType.DEF_METHOD)

        field_item = items_container.def_items[3]
        self.assertEqual(field_item.name, "STATIC_FIELD")
        self.assertEqual(field_item.get_namespace(), "testmod.ABC")
        self.assertEqual(field_item.type, DefItemType.MEMBER)

        self.assertIn(main_item, items_container.use_dict)

        ctor_uses = items_container.use_dict[main_item]
        self.assertEqual(len(ctor_uses), 1)
        self.assertEqual(ctor_uses[0].name, "STATIC_FIELD")
        self.assertEqual(ctor_uses[0].type, DefItemType.MEMBER)

    def test_analyze_var_infer(self):
        code = """\
class ABC2:
    def __init__(self):
        self.field1 = {}

def get_object():
    return ABC2()

def main():
    item2 = get_object()
    item2.field1.get("aaa")
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 6)

        self.assertEqual(def_list[0], ("testmod", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("testmod.ABC2", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("testmod.ABC2.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("testmod.get_object", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[4], ("testmod.main", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[5], ("testmod.ABC2.field1", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 4)

        self.assertEqual(use_list[0], ("testmod.ABC2.__init__", "testmod.ABC2.field1"))
        self.assertEqual(use_list[1], ("testmod.get_object", "testmod.ABC2.__init__"))
        self.assertEqual(use_list[2], ("testmod.main", "testmod.get_object"))
        self.assertEqual(use_list[3], ("testmod.main", "testmod.ABC2.field1"))

    def test_analyze_call_infer(self):
        code = """\
class ABC2:
    def __init__(self):
        self.field1 = {}

def get_object():
    return ABC2()

def main():
    get_object().field1.get("aaa")
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 6)

        self.assertEqual(def_list[0], ("testmod", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("testmod.ABC2", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("testmod.ABC2.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("testmod.get_object", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[4], ("testmod.main", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[5], ("testmod.ABC2.field1", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 4)

        self.assertEqual(use_list[0], ("testmod.ABC2.__init__", "testmod.ABC2.field1"))
        self.assertEqual(use_list[1], ("testmod.get_object", "testmod.ABC2.__init__"))
        self.assertEqual(use_list[2], ("testmod.main", "testmod.get_object"))
        self.assertEqual(use_list[3], ("testmod.main", "testmod.ABC2.field1"))

    def test_analyze_field_infer(self):
        code = """\
class ABC1:
    def execute(self):
        pass

class ABC2:
    def __init__(self, data_manager: ABC1):
        self.data_manager: ABC1 = data_manager

    def access_data(self):
        return self.data_manager.execute()
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 7)

        self.assertEqual(def_list[0], ("testmod", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("testmod.ABC1", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("testmod.ABC1.execute", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("testmod.ABC2", DefItemType.CLASS))
        self.assertEqual(def_list[4], ("testmod.ABC2.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[5], ("testmod.ABC2.access_data", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[6], ("testmod.ABC2.data_manager", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 3)

        self.assertEqual(use_list[0], ("testmod.ABC2.__init__", "testmod.ABC2.data_manager"))
        self.assertEqual(use_list[1], ("testmod.ABC2.access_data", "testmod.ABC2.data_manager"))
        self.assertEqual(use_list[2], ("testmod.ABC2.access_data", "testmod.ABC1.execute"))

    def test_analyze_chained(self):
        code = """\
class ABC2:
    def __init__(self):
        self.field1 = {}

class ABC3:
    def __init__(self):
        self.field2 = ABC2()

def main():
    item3 = ABC3()
    item3.field2.field1.get("aaa")
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 8)

        self.assertEqual(def_list[0], ("testmod", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("testmod.ABC2", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("testmod.ABC2.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("testmod.ABC3", DefItemType.CLASS))
        self.assertEqual(def_list[4], ("testmod.ABC3.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[5], ("testmod.main", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[6], ("testmod.ABC2.field1", DefItemType.MEMBER))
        self.assertEqual(def_list[7], ("testmod.ABC3.field2", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 6)

        self.assertEqual(use_list[0], ("testmod.ABC2.__init__", "testmod.ABC2.field1"))
        self.assertEqual(use_list[1], ("testmod.ABC3.__init__", "testmod.ABC3.field2"))
        self.assertEqual(use_list[2], ("testmod.ABC3.__init__", "testmod.ABC2.__init__"))
        self.assertEqual(use_list[3], ("testmod.main", "testmod.ABC3.__init__"))
        self.assertEqual(use_list[4], ("testmod.main", "testmod.ABC3.field2"))
        self.assertEqual(use_list[5], ("testmod.main", "testmod.ABC2.field1"))

    def test_analyze_chained_call(self):
        code = """\
class ABC2:
    def __init__(self):
        self.field1 = {}

class ABC3:
    def __init__(self):
        self.field2 = ABC2()

    def get_field(self):
        return self.field2

def main():
    item3 = ABC3()
    item3.get_field().field1.get("aaa")
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 9)

        self.assertEqual(def_list[0], ("testmod", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("testmod.ABC2", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("testmod.ABC2.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("testmod.ABC3", DefItemType.CLASS))
        self.assertEqual(def_list[4], ("testmod.ABC3.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[5], ("testmod.ABC3.get_field", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[6], ("testmod.main", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[7], ("testmod.ABC2.field1", DefItemType.MEMBER))
        self.assertEqual(def_list[8], ("testmod.ABC3.field2", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 7)

        self.assertEqual(use_list[0], ("testmod.ABC2.__init__", "testmod.ABC2.field1"))
        self.assertEqual(use_list[1], ("testmod.ABC3.__init__", "testmod.ABC3.field2"))
        self.assertEqual(use_list[2], ("testmod.ABC3.__init__", "testmod.ABC2.__init__"))
        self.assertEqual(use_list[3], ("testmod.ABC3.get_field", "testmod.ABC3.field2"))
        self.assertEqual(use_list[4], ("testmod.main", "testmod.ABC3.__init__"))
        self.assertEqual(use_list[5], ("testmod.main", "testmod.ABC3.get_field"))
        self.assertEqual(use_list[6], ("testmod.main", "testmod.ABC2.field1"))

    def test_analyze_return_constant(self):
        code = """\
def execute():
    return "xxx"
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 2)
        self.assertEqual(len(items_container.use_dict), 0)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        abc_item = items_container.def_items[1]
        self.assertEqual(abc_item.name, "execute")
        self.assertEqual(abc_item.get_namespace(), "testmod")
        self.assertEqual(abc_item.type, DefItemType.DEF_METHOD)

    def test_analyze_return_variable(self):
        code = """\
def execute():
    value = "xxx"
    return value
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 2)
        self.assertEqual(len(items_container.use_dict), 0)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

        abc_item = items_container.def_items[1]
        self.assertEqual(abc_item.name, "execute")
        self.assertEqual(abc_item.get_namespace(), "testmod")
        self.assertEqual(abc_item.type, DefItemType.DEF_METHOD)

    def test_analyze_import(self):
        code = """\
import os
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 1)
        self.assertEqual(len(items_container.use_dict), 0)

    def test_analyze_importfrom(self):
        code = """\
from enum import Enum
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 1)
        self.assertEqual(len(items_container.use_dict), 0)

    def test_analyze_typehint(self):
        code = """\
value: int = 123
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 1)
        self.assertEqual(len(items_container.use_dict), 0)

        mod_item = items_container.def_items[0]
        self.assertEqual(mod_item.type, DefItemType.MODULE)

    def test_analyze_while(self):
        code = """\
class ABC:
    FIELD_0 = 0
    FIELD_1 = 0
    FIELD_2 = 0

while ABC.FIELD_0 > 0:
    ABC.FIELD_1 = 2
else:
    ABC.FIELD_2 = 3
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        self.assertEqual(len(items_container.def_items), 5)
        self.assertEqual(len(items_container.use_dict), 1)

        mod_def_item = items_container.def_items[0]
        self.assertEqual(mod_def_item.name, "testmod")
        self.assertEqual(mod_def_item.get_namespace(), "")
        self.assertEqual(mod_def_item.type, DefItemType.MODULE)

        def_item = items_container.def_items[1]
        self.assertEqual(def_item.name, "ABC")
        self.assertEqual(def_item.get_namespace(), "testmod")
        self.assertEqual(def_item.type, DefItemType.CLASS)

        def_item = items_container.def_items[2]
        self.assertEqual(def_item.name, "FIELD_0")
        self.assertEqual(def_item.get_namespace(), "testmod.ABC")
        self.assertEqual(def_item.type, DefItemType.MEMBER)

        def_item = items_container.def_items[3]
        self.assertEqual(def_item.name, "FIELD_1")
        self.assertEqual(def_item.get_namespace(), "testmod.ABC")
        self.assertEqual(def_item.type, DefItemType.MEMBER)

        def_item = items_container.def_items[4]
        self.assertEqual(def_item.name, "FIELD_2")
        self.assertEqual(def_item.get_namespace(), "testmod.ABC")
        self.assertEqual(def_item.type, DefItemType.MEMBER)

        self.assertIn(mod_def_item, items_container.use_dict)

        mod_uses = items_container.use_dict[mod_def_item]
        self.assertEqual(len(mod_uses), 3)
        self.assertEqual(mod_uses[0].name, "FIELD_0")
        self.assertEqual(mod_uses[1].name, "FIELD_1")
        self.assertEqual(mod_uses[2].name, "FIELD_2")

    def test_analyze_listcompreh_call(self):
        code = """\
class ABC:
    def get_data(self):
        return "1234567890"

    def execute(self):
        data_list = [ item for item in self.get_data() ]
        return data_list
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 4)

        self.assertEqual(def_list[0], ("testmod", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("testmod.ABC", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("testmod.ABC.get_data", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("testmod.ABC.execute", DefItemType.DEF_METHOD))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 1)

        self.assertEqual(use_list[0], ("testmod.ABC.execute", "testmod.ABC.get_data"))

    def test_analyze_subscript(self):
        code = """\
class ABC:
    def execute(self):
        pass

items = [ABC()]
items[0].execute()
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 4)

        self.assertEqual(def_list[0], ("testmod", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("testmod.ABC", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("testmod.ABC.execute", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("testmod.ABC.__init__", DefItemType.DEF_METHOD))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 2)

        self.assertEqual(use_list[0], ("testmod", "testmod.ABC.__init__"))
        self.assertEqual(use_list[1], ("testmod", "testmod.ABC.execute"))

    def test_analyze_argument(self):
        code = """\
from threading import Thread

def execute():
    pass

thread = Thread(target=execute, args=[])
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 2)

        self.assertEqual(def_list[0], ("testmod", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("testmod.execute", DefItemType.DEF_METHOD))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 1)

        self.assertEqual(use_list[0], ("testmod", "testmod.execute"))
