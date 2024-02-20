#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import os
import unittest

from testastgraph.sample import get_data_root_path

from astgraph.pyanwrap import draw_graph
from astgraph.treeparser import TreeParser, DefItemType


def draw(parser, svg_out_path="/tmp/graph.svg"):
    draw_graph(parser.items.def_items, parser.items.use_dict, svg_out_path)


def print_ast(parser):
    for astroid_mod in parser.items.mod_dict.values():
        ast_tree = astroid_mod.repr_tree()
        print(f"AST tree:\n{ast_tree}")


class TreeParserMultifileTest(unittest.TestCase):
    def test_analyze_files_importfrom(self):
        data_root_path = get_data_root_path()
        files_list = []
        files_list.append(os.path.join(data_root_path, "code", "multifileimportfrom", "modulea.py"))
        files_list.append(os.path.join(data_root_path, "code", "multifileimportfrom", "item.py"))

        parser = TreeParser()
        parser.analyze_files(files_list)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 6)

        self.assertEqual(def_list[0], ("multifileimportfrom.modulea", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("multifileimportfrom.modulea.main", DefItemType.MEMBER))
        self.assertEqual(def_list[2], ("multifileimportfrom.item", DefItemType.MODULE))
        self.assertEqual(def_list[3], ("multifileimportfrom.item.Item", DefItemType.CLASS))
        self.assertEqual(def_list[4], ("multifileimportfrom.item.Item.__init__", DefItemType.MEMBER))
        self.assertEqual(def_list[5], ("multifileimportfrom.item.Item.do_work", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 2)

        self.assertEqual(use_list[0], ("multifileimportfrom.modulea.main", "multifileimportfrom.item.Item.__init__"))
        self.assertEqual(use_list[1], ("multifileimportfrom.modulea.main", "multifileimportfrom.item.Item.do_work"))

    def test_analyze_files_importdirect(self):
        data_root_path = get_data_root_path()
        files_list = []
        files_list.append(os.path.join(data_root_path, "code", "multifileimport", "modulea.py"))
        files_list.append(os.path.join(data_root_path, "code", "multifileimport", "item.py"))

        parser = TreeParser()
        parser.analyze_files(files_list)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 6)

        self.assertEqual(def_list[0], ("multifileimport.modulea", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("multifileimport.modulea.main", DefItemType.MEMBER))
        self.assertEqual(def_list[2], ("multifileimport.item", DefItemType.MODULE))
        self.assertEqual(def_list[3], ("multifileimport.item.Item", DefItemType.CLASS))
        self.assertEqual(def_list[4], ("multifileimport.item.Item.__init__", DefItemType.MEMBER))
        self.assertEqual(def_list[5], ("multifileimport.item.Item.do_work", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 2)

        self.assertEqual(use_list[0], ("multifileimport.modulea.main", "multifileimport.item.Item.__init__"))
        self.assertEqual(use_list[1], ("multifileimport.modulea.main", "multifileimport.item.Item.do_work"))

    def test_analyze_files_partial(self):
        data_root_path = get_data_root_path()
        file1 = os.path.join(data_root_path, "code", "multifileimportfrom", "modulea.py")
        files_list = [file1]

        parser = TreeParser()
        parser.analyze_files(files_list)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 2)

        self.assertEqual(def_list[0], ("multifileimportfrom.modulea", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("multifileimportfrom.modulea.main", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 0)
