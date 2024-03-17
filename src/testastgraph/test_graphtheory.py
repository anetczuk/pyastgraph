#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import unittest

from astgraph.graphtheory import get_root_items, visit_graph


class GraphTheoryTest(unittest.TestCase):
    def test_get_root_items_simple(self):
        edges_dict = {1: [2]}
        root_items = get_root_items(edges_dict)
        self.assertEqual(root_items, [1])

    def test_get_root_items_loop(self):
        edges_dict = {1: [2], 3: [4], 4: [3]}
        root_items = get_root_items(edges_dict)
        self.assertEqual(root_items, [1, 3])

    def test_visit_graph_simple(self):
        edges_dict = {1: [2], 2: [3]}
        nodes_list = []
        visit_graph(edges_dict, 1, nodes_list.append)
        self.assertEqual(nodes_list, [1, 2, 3])

    def test_visit_graph_loop(self):
        edges_dict = {1: [2], 3: [4], 4: [3]}

        nodes_list = []
        visit_graph(edges_dict, 1, nodes_list.append)
        self.assertEqual(nodes_list, [1, 2])

        nodes_list = []
        visit_graph(edges_dict, 3, nodes_list.append)
        self.assertEqual(nodes_list, [3, 4])
