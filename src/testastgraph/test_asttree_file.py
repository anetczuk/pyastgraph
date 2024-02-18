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
    astroid_tree = list(parser.items.mod_dict.values())[0]
    ast_tree = astroid_tree.repr_tree()
    print(f"AST tree:\n{ast_tree}")


class TreeParserMultifileTest(unittest.TestCase):
    def test_analyze_files(self):
        data_root_path = get_data_root_path()
        file1 = os.path.join(data_root_path, "code", "multifile", "modulea.py")
        file2 = os.path.join(data_root_path, "code", "multifile", "item.py")
        files_list = [file1, file2]

        parser = TreeParser()
        parser.analyze_files(files_list)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 6)

        self.assertEqual(def_list[0], ("multifile.modulea", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("multifile.modulea.main", DefItemType.MEMBER))
        self.assertEqual(def_list[2], ("multifile.item", DefItemType.MODULE))
        self.assertEqual(def_list[3], ("multifile.item.Item", DefItemType.CLASS))
        self.assertEqual(def_list[4], ("multifile.item.Item.__init__", DefItemType.MEMBER))
        self.assertEqual(def_list[5], ("multifile.item.Item.do_work", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 2)

        self.assertEqual(use_list[0], ("multifile.modulea.main", "multifile.item.Item.__init__"))
        self.assertEqual(use_list[1], ("multifile.modulea.main", "multifile.item.Item.do_work"))

    def test_analyze_files_partial(self):
        data_root_path = get_data_root_path()
        file1 = os.path.join(data_root_path, "code", "multifile", "modulea.py")
        files_list = [file1]

        parser = TreeParser()
        parser.analyze_files(files_list)

        # print_ast(parser)
        # draw(parser)

        items_container = parser.items
        def_list = items_container.get_def_list()
        self.assertEqual(len(def_list), 2)

        self.assertEqual(def_list[0], ("multifile.modulea", DefItemType.MODULE))
        self.assertEqual(def_list[1], ("multifile.modulea.main", DefItemType.MEMBER))

        use_list = items_container.get_use_list()
        self.assertEqual(len(use_list), 0)
