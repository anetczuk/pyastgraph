#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import ast

from graphviz import Digraph


def draw_ast_graph(input_file, output_file):
    with open(input_file, encoding="utf-8") as in_file:
        code = in_file.read()

    dot_graph = generate_dot_graph(code)
    # render the Digraph as a PNG file
    dot_graph.format = "png"
    dot_graph.render(output_file, view=False)


def generate_dot_graph(content):
    dot_graph = Digraph()
    tree = ast.parse(content)
    add_node(dot_graph, tree)
    return dot_graph


def add_node(dot_graph, node, parent=None):
    if isinstance(node, ast.ImportFrom):
        return

    if isinstance(parent, ast.FunctionDef):
        if isinstance(node, ast.Constant):
            # skip doc string
            return
        if isinstance(node, ast.arguments):
            # skip arguments definition of function
            return

    if isinstance(node, ast.Expr):
        # reduce Expr
        add_node(dot_graph, node.value, parent)
        return

    node_name = str(node.__class__.__name__)
    if hasattr(node, "id"):
        node_name = f"{node_name}: {node.id}"
    if hasattr(node, "name"):
        node_name = f"{node_name}: {node.name}"
    if hasattr(node, "attr"):
        node_name = f"{node_name}: {node.attr}"
    if hasattr(node, "value"):
        if isinstance(node.value, str):
            node_name = f"{node_name}: {node.value}"
    if hasattr(node, "arg"):
        node_name = f"{node_name}: {node.arg}"

    dot_graph.node(str(id(node)), node_name)
    if parent:
        dot_graph.edge(str(id(parent)), str(id(node)))
    for child in ast.iter_child_nodes(node):
        add_node(dot_graph, child, node)
