#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import logging

from attrdict import AttrDict

from pyan.node import make_safe_label
from pyan.visgraph import VisualGraph
from pyan.writers import DotWriter, SVGWriter


pyan_logger = logging.getLogger("pyan")
pyan_logger.setLevel(logging.WARN)
# pyan_logger.setLevel(logging.DEBUG)


def draw_graph(def_items, use_dict, out_svg_file_path=None, out_dot_file_path=None):
    graph_options = {
        "draw_defines": True,
        "draw_uses": True,
        "colored": True,
        "grouped_alt": False,
        "grouped": True,
        # "grouped_alt": True,
        # "grouped": False,
        "nested_groups": True,
        "annotated": False,
    }

    node_translation_map = {}

    pyan_nodes_dict = {}
    for def_item in def_items:
        full_name = def_item.get_full_name()
        nodes_list = pyan_nodes_dict.get(full_name, None)
        if nodes_list is None:
            nodes_list = []
            pyan_nodes_dict[full_name] = nodes_list

        node = PyanNodeMock()
        node.namespace = def_item.get_namespace()
        node.name = def_item.get_name()
        node.filename = def_item.get_filename()
        nodes_list.append(node)

        node_translation_map[def_item] = node

    pyan_def_edges_dict = {}
    for def_item in def_items:
        def_parent = def_item.parent
        if def_parent is None:
            continue
        node = node_translation_map.get(def_item)
        if node is None:
            continue
        node_parent = node_translation_map.get(def_parent)
        if node_parent is None:
            continue
        edges_list = pyan_def_edges_dict.get(node_parent, None)
        if edges_list is None:
            edges_list = []
            pyan_def_edges_dict[node_parent] = edges_list
        edges_list.append(node)

    pyan_use_edges_dict = {}
    for use_item, call_list in use_dict.items():
        use_node = node_translation_map.get(use_item)
        if use_node is None:
            continue
        for call_item in call_list:
            call_node = node_translation_map.get(call_item)
            if call_node is None:
                continue
            edges_list = pyan_use_edges_dict.get(use_node, None)
            if edges_list is None:
                edges_list = []
                pyan_use_edges_dict[use_node] = edges_list
            edges_list.append(call_node)

    pyan_def_graph_dict = {
        "nodes": pyan_nodes_dict,
        "defines_edges": pyan_def_edges_dict,
        "uses_edges": pyan_use_edges_dict,
    }
    pyan_def_graph_obj = AttrDict(pyan_def_graph_dict)

    graph = VisualGraph.from_visitor(pyan_def_graph_obj, options=graph_options, logger=pyan_logger)

    if out_dot_file_path:
        writer = DotWriter(graph, options=["rankdir=TB"], output=out_dot_file_path, logger=pyan_logger)
        writer.run()

    if out_svg_file_path:
        writer = SVGWriter(graph, options=["rankdir=TB"], output=out_svg_file_path, logger=pyan_logger)
        writer.run()


# fake pyan node by implementing required members
class PyanNodeMock:
    def __init__(self):
        self.defined = True  # should be presented on graph?
        self.namespace = ""
        self.name = None
        self.filename = None
        self.flavor = None  # not used

    def get_name(self):
        if self.namespace == "":
            return self.name
        if self.namespace is None:
            return "*." + self.name
        return self.namespace + "." + self.name

    def get_short_name(self):
        return self.name

    def get_level(self):
        if self.namespace == "":
            return 0
        return 1 + self.namespace.count(".")

    def get_label(self):
        return make_safe_label(self.get_name())

    def get_namespace_label(self):
        return make_safe_label(self.namespace)
