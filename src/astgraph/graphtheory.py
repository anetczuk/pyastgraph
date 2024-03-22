#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

from typing import Set, Any


def get_root_items(edges_dict):
    all_calles = []
    for items in edges_dict.values():
        all_calles.extend(items)
    root_items = [item for item in edges_dict.keys() if item not in all_calles]

    root_connected = set()
    for root in root_items:
        subitems = get_connected(edges_dict, root)
        root_connected.update(subitems)

    loop_items = [item for item in edges_dict.keys() if item in all_calles]
    for item in loop_items:
        if item in root_connected:
            continue
        # first loop item - new root found
        root_items.append(item)
        subitems = get_connected(edges_dict, item)
        root_connected.update(subitems)

    return root_items


# get all connected nodes starting from 'node'
def get_connected(edges_dict, node):
    connected_list = [node]
    visited_items = set()
    index = 0
    while index < len(connected_list):
        item = connected_list[index]
        subitems = edges_dict.get(item, [])
        for sub in subitems:
            if sub in visited_items:
                continue
            visited_items.add(sub)
            connected_list.append(sub)
        index += 1
    return connected_list


# ==================================================================


class Visitor:
    def __init__(self):
        self._edges_dict = {}
        self._callback = None
        self._visited = set()

    def visit(self, edges_dict, start_node, node_callback):
        self._edges_dict = edges_dict
        self._callback = node_callback
        self._visited = set()
        self._visit_node(start_node)

    def _visit_node(self, node):
        if node in self._visited:
            return
        self._visited.add(node)
        self._callback(node)

        sub_list = self._edges_dict.get(node, [])
        for item in sub_list:
            self._visit_node(item)


def visit_graph(edges_dict, start_node, node_callback):
    visitor = Visitor()
    visitor.visit(edges_dict, start_node, node_callback)


def flatten_to_list(edges_dict):
    ret_list = set()
    for item in edges_dict:
        visit_graph(edges_dict, item, ret_list.add)
    return ret_list


# 'graph_list' - list of top-level graph items
# 'children_getter' - getter for children of graph items
def convert_to_list(graph_list, children_getter):
    connected_list = graph_list
    visited_items = set()
    index = 0
    while index < len(connected_list):
        item = connected_list[index]
        subitems = children_getter(item)
        for sub in subitems:
            if sub in visited_items:
                continue
            visited_items.add(sub)
            connected_list.append(sub)
        index += 1
    return connected_list


def reverse_graph(edges_dict):
    ret_dict = {}
    for node, subnodes_list in edges_dict.items():
        for subnode in subnodes_list:
            sub_list = ret_dict.get(subnode, [])
            if not sub_list:
                ret_dict[subnode] = sub_list
            sub_list.append(node)
    return ret_dict


def join_graph(target_edges_dict, source_edges_dict):
    for node, sub_list in source_edges_dict.items():
        down_list = target_edges_dict.get(node, None)
        if down_list is None:
            target_edges_dict[node] = sub_list
            continue
        down_list.extend(sub_list)
    return target_edges_dict


# ==================================================================


class Filter:
    def __init__(self, filter_list):
        self.filter_list = filter_list

    # override if needed
    def is_matching(self, item):
        return self._is_matching(item)

    def _is_matching(self, item):
        for pattern in self.filter_list:
            if pattern.match(item):
                return True
        return False


# list of compiled regex-es
def filter_down(edges_dict, filter_obj: Filter):
    filtered_nodes: Set[Any] = set()
    for from_node in edges_dict.keys():
        if not filter_obj.is_matching(from_node):
            continue
        connected_nodes = get_connected(edges_dict, from_node)
        filtered_nodes.update(connected_nodes)

    ret_edges = {}
    for from_node, sub_nodes in edges_dict.items():
        if from_node in filtered_nodes:
            ret_edges[from_node] = sub_nodes

    return ret_edges


# list of compiled regex-es
def filter_up(edges_dict, filter_obj: Filter):
    rev_graph = reverse_graph(edges_dict)
    subgraph = filter_down(rev_graph, filter_obj)
    return reverse_graph(subgraph)


# list of compiled regex-es
def filter_updown(edges_dict, filter_obj: Filter):
    down_graph = filter_down(edges_dict, filter_obj)
    up_graph = filter_up(edges_dict, filter_obj)
    join_graph(down_graph, up_graph)
    return down_graph
