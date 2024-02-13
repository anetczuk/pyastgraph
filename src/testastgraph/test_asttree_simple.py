#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import unittest

# from astgraph.pyanwrap import draw_graph
from astgraph.treeparser import TreeParser, DefItemType


class TreeParserTest(unittest.TestCase):

    def test_analyze_variable(self):
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code="aaa = 5")

        items_container = parser.items
        self.assertEqual( len(items_container.def_items), 1 )
        self.assertEqual( len(items_container.use_dict), 0 )

        item = items_container.def_items[0]
        self.assertEqual( item.name, "testmod" )
        self.assertEqual( item.get_namespace(), "" )
        self.assertEqual( item.type, DefItemType.MODULE )

    def test_analyze_func(self):
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code="""\
def func():
    pass
""")

        items_container = parser.items
        self.assertEqual( len(items_container.def_items), 2 )
        self.assertEqual( len(items_container.use_dict), 0 )

        self.assertEqual( items_container.def_items[0].type, DefItemType.MODULE )

        item = items_container.def_items[1]
        self.assertEqual( item.name, "func" )
        self.assertEqual( item.get_namespace(), "testmod" )
        self.assertEqual( item.type, DefItemType.MEMBER )

    def test_analyze_func_call(self):
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code="""\
def func():
    pass

func()
""")

        items_container = parser.items
        self.assertEqual( len(items_container.def_items), 2 )
        self.assertEqual( len(items_container.use_dict), 1 )

        mod_item = items_container.def_items[0]
        self.assertEqual( mod_item.type, DefItemType.MODULE )

        item = items_container.def_items[1]
        self.assertEqual( item.name, "func" )
        self.assertEqual( item.get_namespace(), "testmod" )
        self.assertEqual( item.type, DefItemType.MEMBER )

        mod_uses = items_container.use_dict[mod_item]
        self.assertEqual( len(mod_uses), 1 )
        self.assertEqual( mod_uses[0].name, "func" )
        self.assertEqual( mod_uses[0].type, DefItemType.MEMBER )

    def test_analyze_func_call_02(self):
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code="""\
def func_a():
    pass

def func_b():
    func_a()
""")

        items_container = parser.items
        self.assertEqual( len(items_container.def_items), 3 )
        self.assertEqual( len(items_container.use_dict), 1 )

        mod_item = items_container.def_items[0]
        self.assertEqual( mod_item.type, DefItemType.MODULE )

        func_a_item = items_container.def_items[1]
        self.assertEqual( func_a_item.name, "func_a" )
        self.assertEqual( func_a_item.get_namespace(), "testmod" )
        self.assertEqual( func_a_item.type, DefItemType.MEMBER )

        func_b_item = items_container.def_items[2]
        self.assertEqual( func_b_item.name, "func_b" )
        self.assertEqual( func_b_item.get_namespace(), "testmod" )
        self.assertEqual( func_b_item.type, DefItemType.MEMBER )

        self.assertNotIn(mod_item, items_container.use_dict )
        self.assertNotIn(func_a_item, items_container.use_dict )
        self.assertIn(func_b_item, items_container.use_dict )

        faunc_b_uses = items_container.use_dict[func_b_item]
        self.assertEqual( len(faunc_b_uses), 1 )
        self.assertEqual( faunc_b_uses[0], func_a_item )

    def test_analyze_func_call_02_forward(self):
        # parse code with function declared after it's use

        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code="""\
def func_a():
    func_b()

def func_b():
    pass
""")

        items_container = parser.items
        self.assertEqual( len(items_container.def_items), 3 )
        self.assertEqual( len(items_container.use_dict), 1 )

        mod_item = items_container.def_items[0]
        self.assertEqual( mod_item.type, DefItemType.MODULE )

        func_a_item = items_container.def_items[1]
        self.assertEqual( func_a_item.name, "func_a" )
        self.assertEqual( func_a_item.get_namespace(), "testmod" )
        self.assertEqual( func_a_item.type, DefItemType.MEMBER )

        func_b_item = items_container.def_items[2]
        self.assertEqual( func_b_item.name, "func_b" )
        self.assertEqual( func_b_item.get_namespace(), "testmod" )
        self.assertEqual( func_b_item.type, DefItemType.MEMBER )

        self.assertNotIn(mod_item, items_container.use_dict )
        self.assertIn(func_a_item, items_container.use_dict )
        self.assertNotIn(func_b_item, items_container.use_dict )

        func_a_uses = items_container.use_dict[func_a_item]
        self.assertEqual( len(func_a_uses), 1 )
        self.assertEqual( func_a_uses[0].name, "func_b" )
        self.assertEqual( func_a_uses[0].type, DefItemType.MEMBER )

    def test_analyze_func_call_recursive(self):
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code="""\
def func_a():
    func_a()
""")

        items_container = parser.items
        self.assertEqual( len(items_container.def_items), 2 )
        self.assertEqual( len(items_container.use_dict), 1 )

        mod_item = items_container.def_items[0]
        self.assertEqual( mod_item.type, DefItemType.MODULE )

        func_a_item = items_container.def_items[1]
        self.assertEqual( func_a_item.name, "func_a" )
        self.assertEqual( func_a_item.get_namespace(), "testmod" )
        self.assertEqual( func_a_item.type, DefItemType.MEMBER )

        self.assertNotIn(mod_item, items_container.use_dict )
        self.assertIn(func_a_item, items_container.use_dict )

        func_a_uses = items_container.use_dict[func_a_item]
        self.assertEqual( len(func_a_uses), 1 )
        self.assertEqual( func_a_uses[0].name, "func_a" )
        self.assertEqual( func_a_uses[0].type, DefItemType.MEMBER )

    def test_analyze_classdef(self):
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code="""\
class ABC:
    def __init__(self):
        pass
""")

        items_container = parser.items
        self.assertEqual( len(items_container.def_items), 3 )
        self.assertEqual( len(items_container.use_dict), 0 )

        mod_item = items_container.def_items[0]
        self.assertEqual( mod_item.type, DefItemType.MODULE )

        abc_item = items_container.def_items[1]
        self.assertEqual( abc_item.name, "ABC" )
        self.assertEqual( abc_item.get_namespace(), "testmod" )
        self.assertEqual( abc_item.type, DefItemType.CLASS )

        ctor_item = items_container.def_items[2]
        self.assertEqual( ctor_item.name, "__init__" )
        self.assertEqual( ctor_item.get_namespace(), "testmod.ABC" )
        self.assertEqual( ctor_item.type, DefItemType.MEMBER )

    def test_analyze_field_AssignAttr(self):
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code="""\
class ABC:
    def __init__(self):
        self.data_field = 'xxx'
""")

        items_container = parser.items
        self.assertEqual( len(items_container.def_items), 4 )
        self.assertEqual( len(items_container.use_dict), 1 )

        mod_item = items_container.def_items[0]
        self.assertEqual( mod_item.type, DefItemType.MODULE )

        abc_item = items_container.def_items[1]
        self.assertEqual( abc_item.name, "ABC" )
        self.assertEqual( abc_item.get_namespace(), "testmod" )
        self.assertEqual( abc_item.type, DefItemType.CLASS )

        ctor_item = items_container.def_items[2]
        self.assertEqual( ctor_item.name, "__init__" )
        self.assertEqual( ctor_item.get_namespace(), "testmod.ABC" )
        self.assertEqual( ctor_item.type, DefItemType.MEMBER )

        field_item = items_container.def_items[3]
        self.assertEqual( field_item.name, "data_field" )
        self.assertEqual( field_item.get_namespace(), "testmod.ABC" )
        self.assertEqual( field_item.type, DefItemType.MEMBER )

        self.assertIn(ctor_item, items_container.use_dict )

        ctor_uses = items_container.use_dict[ctor_item]
        self.assertEqual( len(ctor_uses), 1 )
        self.assertEqual( ctor_uses[0].name, "data_field" )
        self.assertEqual( ctor_uses[0].type, DefItemType.MEMBER )

    def test_analyze_access_static(self):
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code="""\
class ABC:
    STATIC_FIELD = "initial_value"

def main():
    ABC.STATIC_FIELD = "main_value"
""")

        items_container = parser.items
        self.assertEqual( len(items_container.def_items), 4 )
        self.assertEqual( len(items_container.use_dict), 1 )

        mod_item = items_container.def_items[0]
        self.assertEqual( mod_item.type, DefItemType.MODULE )

        abc_item = items_container.def_items[1]
        self.assertEqual( abc_item.name, "ABC" )
        self.assertEqual( abc_item.get_namespace(), "testmod" )
        self.assertEqual( abc_item.type, DefItemType.CLASS )

        field_item = items_container.def_items[2]
        self.assertEqual( field_item.name, "STATIC_FIELD" )
        self.assertEqual( field_item.get_namespace(), "testmod.ABC" )
        self.assertEqual( field_item.type, DefItemType.MEMBER )

        main_item = items_container.def_items[3]
        self.assertEqual( main_item.name, "main" )
        self.assertEqual( main_item.get_namespace(), "testmod" )
        self.assertEqual( main_item.type, DefItemType.MEMBER )

        self.assertIn(main_item, items_container.use_dict )

        ctor_uses = items_container.use_dict[main_item]
        self.assertEqual( len(ctor_uses), 1 )
        self.assertEqual( ctor_uses[0].name, "STATIC_FIELD" )
        self.assertEqual( ctor_uses[0].type, DefItemType.MEMBER )
