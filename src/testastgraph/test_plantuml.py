#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import unittest

from astgraph.treeparser import TreeParser
from astgraph.plantuml import Converter, generate_diagram, convert_to_svg, SequenceGraph, SequenceCall


def draw(sequence_graph, svg_out_path="/tmp/pyastgraph_seq.svg"):
    out_seq_diag_path = f"{svg_out_path}.txt"
    generate_diagram(sequence_graph, out_seq_diag_path)
    convert_to_svg(out_seq_diag_path, svg_out_path)


class ConverterTest(unittest.TestCase):
    def test_convert_classdef_simple(self):
        code = """\
class ABC1:
    def __init__(self):
        self.field1 = {}
        self.execute()

    def execute(self):
        pass
"""
        analyzer = TreeParser()
        analyzer.analyze_code(module_name="testmod", code=code)
        items = analyzer.items

        converter = Converter()
        sequence_graph: SequenceGraph = converter.convert(items.use_dict)

        draw(sequence_graph)

        calls_list = sequence_graph.get_all_calls_flat()
        self.assertEqual(len(calls_list), 3)

        item: SequenceCall = calls_list[0]
        self.assertEqual(item.caller, None)
        self.assertEqual(item.label, "__init__")
        self.assertEqual(item.calles, ["testmod.ABC1"])

        item: SequenceCall = calls_list[1]
        self.assertEqual(item.caller, "testmod.ABC1")
        self.assertEqual(item.label, "field1")
        self.assertEqual(item.calles, [])

        item: SequenceCall = calls_list[2]
        self.assertEqual(item.caller, "testmod.ABC1")
        self.assertEqual(item.label, "execute")
        self.assertEqual(item.calles, ["testmod.ABC1"])

    def test_convert_classdef_recursive(self):
        code = """\
class ABC1:
    def __init__(self):
        self.field1 = {}

    def execute_a(self):
        self.execute_b()

    def execute_b(self):
        self.execute_c()

    def execute_c(self):
        self.execute_a()
"""
        analyzer = TreeParser()
        analyzer.analyze_code(module_name="testmod", code=code)
        items = analyzer.items

        converter = Converter()
        sequence_graph: SequenceGraph = converter.convert(items.use_dict)

        # draw(sequence_graph)

        calls_list = sequence_graph.get_all_calls_flat()
        self.assertEqual(len(calls_list), 6)

        item: SequenceCall = calls_list[0]
        self.assertEqual(item.caller, None)
        self.assertEqual(item.label, "__init__")
        self.assertEqual(item.calles, ["testmod.ABC1"])

        item: SequenceCall = calls_list[1]
        self.assertEqual(item.caller, "testmod.ABC1")
        self.assertEqual(item.label, "field1")
        self.assertEqual(item.calles, [])

        item: SequenceCall = calls_list[2]
        self.assertEqual(item.caller, None)
        self.assertEqual(item.label, "execute_a")
        self.assertEqual(item.calles, ["testmod.ABC1"])

        item: SequenceCall = calls_list[3]
        self.assertEqual(item.caller, "testmod.ABC1")
        self.assertEqual(item.label, "execute_b")
        self.assertEqual(item.calles, ["testmod.ABC1"])

        item: SequenceCall = calls_list[4]
        self.assertEqual(item.caller, "testmod.ABC1")
        self.assertEqual(item.label, "execute_c")
        self.assertEqual(item.calles, ["testmod.ABC1"])

        item: SequenceCall = calls_list[5]
        self.assertEqual(item.caller, "testmod.ABC1")
        self.assertEqual(item.label, "execute_a")
        self.assertEqual(item.calles, ["testmod.ABC1"])

    def test_convert_field(self):
        code = """\
class ABC1:
    def __init__(self):
        self.field1 = {}

item = ABC1()
"""
        analyzer = TreeParser()
        analyzer.analyze_code(module_name="testmod", code=code)
        items = analyzer.items

        converter = Converter()
        sequence_graph: SequenceGraph = converter.convert(items.use_dict)

        draw(sequence_graph)

        calls_list = sequence_graph.get_all_calls_flat()
        self.assertEqual(len(calls_list), 2)

        item: SequenceCall = calls_list[0]
        self.assertEqual(item.caller, "testmod")
        self.assertEqual(item.label, "__init__")
        self.assertEqual(item.calles, ["testmod.ABC1"])

        item: SequenceCall = calls_list[1]
        self.assertEqual(item.caller, "testmod.ABC1")
        self.assertEqual(item.label, "field1")
        self.assertEqual(item.calles, [])

    def test_convert_ctor_call(self):
        code = """\
class ABC1:
    def __init__(self):
        pass

class ABC2:
    def __init__(self):
        self.field2 = ABC1()

item = ABC2()
"""
        analyzer = TreeParser()
        analyzer.analyze_code(module_name="testmod", code=code)
        items = analyzer.items

        converter = Converter()
        sequence_graph: SequenceGraph = converter.convert(items.use_dict)

        draw(sequence_graph)

        calls_list = sequence_graph.get_all_calls_flat()
        self.assertEqual(len(calls_list), 3)

        item: SequenceCall = calls_list[0]
        self.assertEqual(item.caller, "testmod")
        self.assertEqual(item.label, "__init__")
        self.assertEqual(item.calles, ["testmod.ABC2"])

        item: SequenceCall = calls_list[1]
        self.assertEqual(item.caller, "testmod.ABC2")
        self.assertEqual(item.label, "field2")
        self.assertEqual(item.calles, [])

        item: SequenceCall = calls_list[2]
        self.assertEqual(item.caller, "testmod.ABC2")
        self.assertEqual(item.label, "__init__")
        self.assertEqual(item.calles, ["testmod.ABC1"])

    def test_missing_method_def(self):
        code = """\
class Invalid:
    def __init__(self):
        self.data_field = None
        self.execute()
        self.invalid_call()  # non existing method  # pylint: disable=E1101

    def execute(self):
        self.data_field = "xxx"
"""
        analyzer = TreeParser()
        analyzer.analyze_code(module_name="testmod", code=code)
        items = analyzer.items

        converter = Converter()
        sequence_graph: SequenceGraph = converter.convert(items.use_dict)

        draw(sequence_graph)

        calls_list = sequence_graph.get_all_calls_flat()
        self.assertEqual(len(calls_list), 4)

        item: SequenceCall = calls_list[0]
        self.assertEqual(item.caller, None)
        self.assertEqual(item.label, "__init__")
        self.assertEqual(item.calles, ["testmod.Invalid"])

        item: SequenceCall = calls_list[1]
        self.assertEqual(item.caller, "testmod.Invalid")
        self.assertEqual(item.label, "data_field")
        self.assertEqual(item.calles, [])

        item: SequenceCall = calls_list[2]
        self.assertEqual(item.caller, "testmod.Invalid")
        self.assertEqual(item.label, "execute")
        self.assertEqual(item.calles, ["testmod.Invalid"])

        item: SequenceCall = calls_list[3]
        self.assertEqual(item.caller, "testmod.Invalid")
        self.assertEqual(item.label, "data_field")
        self.assertEqual(item.calles, [])

    def test_access_field(self):
        code = """\
class Runner:

    STATIC_FIELD = "initial_value"

    def __init__(self):
        self.instance_field = []


def main():
    runner = Runner()
    runner.instance_field = ["aaa"]
    Runner.STATIC_FIELD = "main_value"


if __name__ == "__main__":
    main()
"""
        analyzer = TreeParser()
        analyzer.analyze_code(module_name="testmod", code=code)
        items = analyzer.items

        converter = Converter()
        sequence_graph: SequenceGraph = converter.convert(items.use_dict)

        draw(sequence_graph)

        calls_list = sequence_graph.get_all_calls_flat()
        self.assertEqual(len(calls_list), 5)

        item: SequenceCall = calls_list[0]
        self.assertEqual(item.caller, "testmod")
        self.assertEqual(item.label, "main")
        self.assertEqual(item.calles, ["testmod"])

        item: SequenceCall = calls_list[1]
        self.assertEqual(item.caller, "testmod")
        self.assertEqual(item.label, "__init__")
        self.assertEqual(item.calles, ["testmod.Runner"])

        item: SequenceCall = calls_list[2]
        self.assertEqual(item.caller, "testmod")
        self.assertEqual(item.label, "instance_field")
        self.assertEqual(item.calles, ["testmod.Runner"])

        item: SequenceCall = calls_list[3]
        self.assertEqual(item.caller, "testmod")
        self.assertEqual(item.label, "STATIC_FIELD")
        self.assertEqual(item.calles, ["testmod.Runner"])

        item: SequenceCall = calls_list[4]
        self.assertEqual(item.caller, "testmod.Runner")
        self.assertEqual(item.label, "instance_field")
        self.assertEqual(item.calles, [])
