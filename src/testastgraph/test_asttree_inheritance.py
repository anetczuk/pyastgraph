#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import os
import unittest

from astgraph.pyanwrap import draw_full_graph
from astgraph.treeparser import TreeParser, DefItemType

from testastgraph.sample import get_data_root_path


def draw(parser, svg_out_path="/tmp/graph.svg"):
    output_dict = {"outsvgfile": svg_out_path}
    defs_list = parser.items.get_def_list()
    draw_full_graph(defs_list, parser.items.use_dict, output_dict)


def print_ast(parser: TreeParser):
    for astroid_mod in parser.items.mod_dict.values():
        ast_tree = astroid_mod.repr_tree()
        print(f"AST tree:\n{ast_tree}")


class TreeParserInheritanceTest(unittest.TestCase):
    def test_analyze_inherit_01(self):
        # inheritance case: implicit constructor in derived class

        data_root_path = get_data_root_path()
        files_list = []
        files_list.append(os.path.join(data_root_path, "code", "inherit", "inherit01.py"))

        parser = TreeParser()
        parser.analyze_files(files_list)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list_info()
        self.assertEqual(len(def_list), 11)

        self.assertEqual(def_list[0], ("inherit.inherit01", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("inherit.inherit01.Base", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("inherit.inherit01.Base.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("inherit.inherit01.Base.do_work", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[4], ("inherit.inherit01.Base.execute_base", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[5], ("inherit.inherit01.Base._execute_priv", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[6], ("inherit.inherit01.Item", DefItemType.CLASS))
        self.assertEqual(def_list[7], ("inherit.inherit01.Item.execute", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[8], ("inherit.inherit01.Item._execute_priv", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[9], ("inherit.inherit01.Base.field", DefItemType.MEMBER))
        self.assertEqual(def_list[10], ("inherit.inherit01.Item.__init__", DefItemType.DEF_METHOD))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 9)

        self.assertEqual(use_list[0], ("inherit.inherit01.Base.__init__", "inherit.inherit01.Base.field"))
        self.assertEqual(use_list[1], ("inherit.inherit01.Base.execute_base", "inherit.inherit01.Base._execute_priv"))
        self.assertEqual(use_list[2], ("inherit.inherit01.Base.execute_base", "inherit.inherit01.Item._execute_priv"))
        self.assertEqual(use_list[3], ("inherit.inherit01.Item.execute", "inherit.inherit01.Base.do_work"))
        self.assertEqual(use_list[4], ("inherit.inherit01.Item.execute", "inherit.inherit01.Base.execute_base"))
        self.assertEqual(use_list[5], ("inherit.inherit01.Item._execute_priv", "inherit.inherit01.Base.do_work"))
        self.assertEqual(use_list[6], ("inherit.inherit01.Item.__init__", "inherit.inherit01.Base.__init__"))
        self.assertEqual(use_list[7], ("inherit.inherit01", "inherit.inherit01.Item.__init__"))
        self.assertEqual(use_list[8], ("inherit.inherit01", "inherit.inherit01.Item.execute"))

    def test_analyze_inherit_super(self):
        # handle call of base class constructor

        code = """\
class Base:
    def __init__(self):
        pass
class Item(Base):
    def __init__(self):
        super().__init__()

item = Item()
"""
        parser = TreeParser()
        parser.analyze_code(module_name="testmod", code=code)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list_info()
        self.assertEqual(len(def_list), 5)

        self.assertEqual(def_list[0], ("testmod", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("testmod.Base", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("testmod.Base.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("testmod.Item", DefItemType.CLASS))
        self.assertEqual(def_list[4], ("testmod.Item.__init__", DefItemType.DEF_METHOD))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 2)

        self.assertEqual(use_list[0], ("testmod.Item.__init__", "testmod.Base.__init__"))
        self.assertEqual(use_list[1], ("testmod", "testmod.Item.__init__"))

    def test_analyze_inherit_02(self):
        # inheritance case: explicit constructor in derived class with call to base class ctor

        data_root_path = get_data_root_path()
        files_list = []
        files_list.append(os.path.join(data_root_path, "code", "inherit", "inherit02.py"))

        parser = TreeParser()
        parser.analyze_files(files_list)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list_info()
        self.assertEqual(len(def_list), 11)

        self.assertEqual(def_list[0], ("inherit.inherit02", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("inherit.inherit02.Base", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("inherit.inherit02.Base.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("inherit.inherit02.Base.do_work", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[4], ("inherit.inherit02.Base.execute_base", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[5], ("inherit.inherit02.Base._execute_priv", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[6], ("inherit.inherit02.Item", DefItemType.CLASS))
        self.assertEqual(def_list[7], ("inherit.inherit02.Item.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[8], ("inherit.inherit02.Item.execute", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[9], ("inherit.inherit02.Item._execute_priv", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[10], ("inherit.inherit02.Base.field", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 9)

        self.assertEqual(use_list[0], ("inherit.inherit02.Base.__init__", "inherit.inherit02.Base.field"))
        self.assertEqual(use_list[1], ("inherit.inherit02.Base.execute_base", "inherit.inherit02.Base._execute_priv"))
        self.assertEqual(use_list[2], ("inherit.inherit02.Base.execute_base", "inherit.inherit02.Item._execute_priv"))
        self.assertEqual(use_list[3], ("inherit.inherit02.Item.__init__", "inherit.inherit02.Base.__init__"))
        self.assertEqual(use_list[4], ("inherit.inherit02.Item.execute", "inherit.inherit02.Base.do_work"))
        self.assertEqual(use_list[5], ("inherit.inherit02.Item.execute", "inherit.inherit02.Base.execute_base"))
        self.assertEqual(use_list[6], ("inherit.inherit02.Item._execute_priv", "inherit.inherit02.Base.do_work"))
        self.assertEqual(use_list[7], ("inherit.inherit02", "inherit.inherit02.Item.__init__"))
        self.assertEqual(use_list[8], ("inherit.inherit02", "inherit.inherit02.Item.execute"))

    def test_analyze_inherit_03(self):
        # inheritance case: explicit constructor in derived class without call to base class ctor

        data_root_path = get_data_root_path()
        files_list = []
        files_list.append(os.path.join(data_root_path, "code", "inherit", "inherit03.py"))

        parser = TreeParser()
        parser.analyze_files(files_list)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list_info()
        self.assertEqual(len(def_list), 11)

        self.assertEqual(def_list[0], ("inherit.inherit03", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("inherit.inherit03.Base", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("inherit.inherit03.Base.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("inherit.inherit03.Base.do_work", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[4], ("inherit.inherit03.Base.execute_base", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[5], ("inherit.inherit03.Base._execute_priv", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[6], ("inherit.inherit03.Item", DefItemType.CLASS))
        self.assertEqual(def_list[7], ("inherit.inherit03.Item.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[8], ("inherit.inherit03.Item.execute", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[9], ("inherit.inherit03.Item._execute_priv", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[10], ("inherit.inherit03.Base.field", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 8)

        self.assertEqual(use_list[0], ("inherit.inherit03.Base.__init__", "inherit.inherit03.Base.field"))
        self.assertEqual(use_list[1], ("inherit.inherit03.Base.execute_base", "inherit.inherit03.Base._execute_priv"))
        self.assertEqual(use_list[2], ("inherit.inherit03.Base.execute_base", "inherit.inherit03.Item._execute_priv"))
        self.assertEqual(use_list[3], ("inherit.inherit03.Item.execute", "inherit.inherit03.Base.do_work"))
        self.assertEqual(use_list[4], ("inherit.inherit03.Item.execute", "inherit.inherit03.Base.execute_base"))
        self.assertEqual(use_list[5], ("inherit.inherit03.Item._execute_priv", "inherit.inherit03.Base.do_work"))
        self.assertEqual(use_list[6], ("inherit.inherit03", "inherit.inherit03.Item.__init__"))
        self.assertEqual(use_list[7], ("inherit.inherit03", "inherit.inherit03.Item.execute"))

    def test_analyze_override_01(self):
        # inheritance case: explicit constructor in derived class without call to base class ctor

        data_root_path = get_data_root_path()
        files_list = []
        files_list.append(os.path.join(data_root_path, "code", "inherit", "override01.py"))

        parser = TreeParser()
        parser.analyze_files(files_list)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list_info()
        self.assertEqual(len(def_list), 8)

        self.assertEqual(def_list[0], ("inherit.override01", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("inherit.override01.Base", DefItemType.CLASS))
        self.assertEqual(def_list[2], ("inherit.override01.Base.execute", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[3], ("inherit.override01.Base.do_work", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[4], ("inherit.override01.Item", DefItemType.CLASS))
        self.assertEqual(def_list[5], ("inherit.override01.Item.do_work", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[6], ("inherit.override01.Item.__init__", DefItemType.DEF_METHOD))
        self.assertEqual(def_list[7], ("inherit.override01.Base.__init__", DefItemType.DEF_METHOD))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 5)

        self.assertEqual(use_list[0], ("inherit.override01.Base.execute", "inherit.override01.Base.do_work"))
        self.assertEqual(use_list[1], ("inherit.override01.Base.execute", "inherit.override01.Item.do_work"))
        self.assertEqual(use_list[2], ("inherit.override01.Item.__init__", "inherit.override01.Base.__init__"))
        self.assertEqual(use_list[3], ("inherit.override01", "inherit.override01.Item.__init__"))
        self.assertEqual(use_list[4], ("inherit.override01", "inherit.override01.Base.execute"))
