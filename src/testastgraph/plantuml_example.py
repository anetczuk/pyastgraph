#!/usr/bin/env python3
#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

try:
    ## following import success only when file is directly executed from command line
    ## otherwise will throw exception when executing as parameter for "python -m"
    # pylint: disable=W0611
    import __init__
except ImportError:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

from astgraph.plantuml import generate_diagram, convert_to_svg, SequenceGraph, SequenceCallList


def main():
    sequence_graph = SequenceGraph()
    sequence_graph.add_actor("AAA", "aaa", "red")
    sequence_graph.add_actor("BBB")

    loop1 = SequenceCallList(0)
    loop1.add_simple_call("AAA", "BBB", "xxx")
    sequence_graph.append_loop(loop1)

    loop2 = SequenceCallList(7)
    loop2.add_simple_call("AAA", "BBB", "yyy")
    sequence_graph.append_loop(loop2)

    loop3 = SequenceCallList(7)
    loop3.add_calles("AAA", ["BBB", "CCC"], "zzz")
    sequence_graph.append_loop(loop3)

    loop4 = SequenceCallList(3)
    call = loop4.add_simple_call("AAA", "BBB", "aaa")
    call.add_simple_subcall("BBB", "CCC", "bbb")
    sequence_graph.append_loop(loop4)

    graph_out_path = "/tmp/seq_graph.plantuml.txt"
    generate_diagram(sequence_graph, graph_out_path)

    svg_out_path = "/tmp/seq_graph.plantuml.svg"
    convert_to_svg(graph_out_path, svg_out_path)

    print("data generated in file:", graph_out_path)
    print("svg generated in file:", svg_out_path)


if __name__ == "__main__":
    main()
