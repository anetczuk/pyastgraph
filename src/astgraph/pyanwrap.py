#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import logging
from typing import List, Dict, Any

from attrdict import AttrDict

from pyan.node import make_safe_label
from pyan.visgraph import VisualGraph
from pyan.writers import DotWriter, SVGWriter, HTMLWriter
from astgraph.treeparser import DefItem, DefItemType, ClassItem


pyan_logger = logging.getLogger("pyan")
pyan_logger.setLevel(logging.WARN)
# pyan_logger.setLevel(logging.DEBUG)

_LOGGER = logging.getLogger(__name__)


def draw_full_graph(def_items: List[DefItem], use_dict: Dict[Any, Any], output_dict=None):
    if not output_dict:
        output_dict = {}

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

    out_edges_num = count_max_edges(use_dict)
    for def_item in def_items:
        child_len = len(def_item.get_items())
        out_edges_num = max(out_edges_num, child_len)

    pyan_def_graph_obj = convert_to_pyan_graph(def_items, use_dict)

    graph = VisualGraph.from_visitor(pyan_def_graph_obj, options=graph_options, logger=pyan_logger)

    out_dot_file_path = output_dict.get("outdotfile")
    out_svg_file_path = output_dict.get("outsvgfile")
    out_html_file_path = output_dict.get("outhtmlfile")

    ranksep = out_edges_num / 12.0
    ranksep = max(ranksep, 1.0)
    options = ["rankdir=TB"]
    options += [f'ranksep="{ranksep}"']

    if out_dot_file_path:
        _LOGGER.info("writing DOT file to %s", out_dot_file_path)
        writer = DotWriter(graph, options=options, output=out_dot_file_path, logger=pyan_logger)
        writer.run()

    if out_svg_file_path:
        _LOGGER.info("writing SVG file to %s", out_svg_file_path)
        writer = SVGWriter(graph, options=options, output=out_svg_file_path, logger=pyan_logger)
        writer.run()

    if out_html_file_path:
        _LOGGER.info("writing HTML file to %s", out_html_file_path)
        writer = HTMLWriter(graph, options=options, output=out_html_file_path, logger=pyan_logger)
        writer.run()


def draw_use_graph(use_dict: Dict[Any, Any], output_dict=None):
    if not output_dict:
        output_dict = {}

    graph_options = {
        "draw_defines": False,
        "draw_uses": True,
        "colored": True,
        "grouped_alt": False,
        "grouped": True,
        # "grouped_alt": True,
        # "grouped": False,
        "nested_groups": True,
        "annotated": False,
    }

    # initialize translation map
    node_translation_map: Dict[DefItem, PyanNodeMock] = {}
    # def_item: DefItem
    for use_item, call_list in use_dict.items():
        copied_list = call_list.copy()
        copied_list.append(use_item)
        for def_item in copied_list:
            if def_item in node_translation_map:
                continue
            node = PyanNodeMock()
            node.namespace = def_item.get_namespace()
            node.name = def_item.get_name()
            node.filename = def_item.get_filename()
            node_translation_map[def_item] = node

    # generate pyan use edges graph
    out_edges_num = 0
    pyan_use_edges_dict: Dict[PyanNodeMock, List[PyanNodeMock]] = {}
    for use_item, call_list in use_dict.items():
        use_node: PyanNodeMock = node_translation_map.get(use_item)
        if use_node is None:
            continue
        for call_item in call_list:
            call_node: PyanNodeMock = node_translation_map.get(call_item)
            if call_node is None:
                continue
            edges_list = pyan_use_edges_dict.get(use_node, None)
            if edges_list is None:
                edges_list = []
                pyan_use_edges_dict[use_node] = edges_list
            edges_list.append(call_node)
            out_edges_num = max(out_edges_num, len(edges_list))

    # generate names dict
    pyan_nodes_dict: Dict[str, List[PyanNodeMock]] = {}
    edge_nodes_list = set()
    # node: PyanNodeMock
    for node, connections in pyan_use_edges_dict.items():
        edge_nodes_list.add(node)
        edge_nodes_list.update(connections)

    # node: PyanNodeMock
    for node in edge_nodes_list:
        full_name = node.get_name()
        nodes_list = pyan_nodes_dict.get(full_name, None)
        if nodes_list is None:
            nodes_list = []
            pyan_nodes_dict[full_name] = nodes_list
        nodes_list.append(node)

    pyan_def_graph_dict = {"nodes": pyan_nodes_dict, "defines_edges": {}, "uses_edges": pyan_use_edges_dict}
    pyan_def_graph_obj = AttrDict(pyan_def_graph_dict)  # recursively convert dict to obj (keys become attributes)

    graph = VisualGraph.from_visitor(pyan_def_graph_obj, options=graph_options, logger=pyan_logger)

    out_dot_file_path = output_dict.get("outdotfile")
    out_svg_file_path = output_dict.get("outsvgfile")
    out_html_file_path = output_dict.get("outhtmlfile")

    ranksep = out_edges_num / 12.0
    ranksep = max(ranksep, 1.0)
    options = ["rankdir=TB"]
    options += [f'ranksep="{ranksep}"']

    if out_dot_file_path:
        _LOGGER.info("writing DOT file to %s", out_dot_file_path)
        writer = DotWriter(graph, options=options, output=out_dot_file_path, logger=pyan_logger)
        writer.run()

    if out_svg_file_path:
        _LOGGER.info("writing SVG file to %s", out_svg_file_path)
        writer = SVGWriter(graph, options=options, output=out_svg_file_path, logger=pyan_logger)
        writer.run()

    if out_html_file_path:
        _LOGGER.info("writing HTML file to %s", out_html_file_path)
        writer = HTMLWriter(graph, options=options, output=out_html_file_path, logger=pyan_logger)
        writer.run()


def convert_to_pyan_graph(def_items: List[DefItem], use_dict: Dict[Any, Any]):
    # initialize translation map
    node_translation_map: Dict[DefItem, PyanNodeMock] = {}
    # def_item: DefItem
    for def_item in def_items:
        pyan_node = PyanNodeMock()
        pyan_node.namespace = def_item.get_namespace()
        pyan_node.name = def_item.get_name()
        pyan_node.filename = def_item.get_filename()
        node_translation_map[def_item] = pyan_node

    # generate pyan def edges graph
    pyan_def_edges_dict: Dict[PyanNodeMock, List[PyanNodeMock]] = {}
    # def_item: DefItem
    for def_item in def_items:
        def_parent: DefItem = def_item.parent
        if def_parent is None:
            continue
        node: PyanNodeMock = node_translation_map.get(def_item)
        if node is None:
            continue

        if isinstance(def_item, ClassItem):
            for def_base in def_item.bases:
                node_base: PyanNodeMock = node_translation_map.get(def_base)
                if node_base is None:
                    continue

                edges_list = pyan_def_edges_dict.get(node, None)
                if edges_list is None:
                    edges_list = []
                    pyan_def_edges_dict[node] = edges_list
                edges_list.append(node_base)

        if def_parent.type is DefItemType.MODULE:
            # do not show module nodes
            continue
        node_parent: PyanNodeMock = node_translation_map.get(def_parent)
        if node_parent is None:
            continue

        edges_list = pyan_def_edges_dict.get(node_parent, None)
        if edges_list is None:
            edges_list = []
            pyan_def_edges_dict[node_parent] = edges_list
        edges_list.append(node)

    # generate pyan use edges graph
    pyan_use_edges_dict: Dict[PyanNodeMock, List[PyanNodeMock]] = {}
    for use_item, call_list in use_dict.items():
        use_node: PyanNodeMock = node_translation_map.get(use_item)
        if use_node is None:
            continue
        for call_item in call_list:
            call_node: PyanNodeMock = node_translation_map.get(call_item)
            if call_node is None:
                continue
            edges_list = pyan_use_edges_dict.get(use_node, None)
            if edges_list is None:
                edges_list = []
                pyan_use_edges_dict[use_node] = edges_list
            edges_list.append(call_node)

    pyan_nodes_dict: Dict[str, List[PyanNodeMock]] = {}
    edge_nodes_list = set()
    # node: PyanNodeMock
    for node, connections in pyan_def_edges_dict.items():
        edge_nodes_list.add(node)
        edge_nodes_list.update(connections)
    for node, connections in pyan_use_edges_dict.items():
        edge_nodes_list.add(node)
        edge_nodes_list.update(connections)

    # node: PyanNodeMock
    for node in edge_nodes_list:
        full_name = node.get_name()
        nodes_list = pyan_nodes_dict.get(full_name, None)
        if nodes_list is None:
            nodes_list = []
            pyan_nodes_dict[full_name] = nodes_list
        nodes_list.append(node)

    pyan_def_graph_dict = {
        "nodes": pyan_nodes_dict,
        "defines_edges": pyan_def_edges_dict,
        "uses_edges": pyan_use_edges_dict,
    }
    pyan_def_graph_obj = AttrDict(pyan_def_graph_dict)  # recursively convert dict to obj (keys become attributes)

    return pyan_def_graph_obj


def count_max_edges(use_dict: Dict[Any, Any]):
    out_edges_num = 0
    for uses_list in use_dict.values():
        out_edges_num = max(out_edges_num, len(uses_list))
    return out_edges_num


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
