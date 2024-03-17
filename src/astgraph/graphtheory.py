#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#


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


def get_connected(edges_dict, node):
    connected_list = [node]
    visited_list = set()
    index = 0
    while index < len(connected_list):
        item = connected_list[index]
        subitems = edges_dict.get(item, [])
        for sub in subitems:
            if sub in visited_list:
                continue
            visited_list.add(sub)
            connected_list.append(sub)
        index += 1
    return connected_list


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


# def get_root_items(edges_dict):
#     all_nodes = set()
#     for item, subitems in edges_dict.items():
#         all_nodes.add(item)
#         all_nodes.extend(subitems)
#     return []
#     # root_items = [ item for item in edges_dict.keys() if item not in all_calles ]
#     # return root_items


# def _get_root_items(self):
#     all_calles = []
#     for items in self.use_dict.values():
#         all_calles.extend(items)
#     root_items = [ item for item in self.use_dict.keys() if item not in all_calles ]
#     return root_items
