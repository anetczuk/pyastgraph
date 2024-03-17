#!/usr/bin/env python3

#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import sys
import os
import logging
import argparse

import pprint

from astgraph.objtodict import obj_to_dict
from astgraph.treeparser import TreeParser
from astgraph.pyanwrap import draw_graph as draw_pyan_graph
from astgraph.plantuml import draw_graph as draw_plantuml_graph


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_LOGGER = logging.getLogger(__name__)


def analyze_code(files_list, output_dict, debug_dump=False):
    analyzer = TreeParser()
    analyzer.analyze_files(files_list)
    items = analyzer.items

    if debug_dump:
        out_svg_file_path = output_dict["outsvgfile"]
        graph_dict = obj_to_dict(items, skip_meta_data=False)
        dict_path = f"{out_svg_file_path}.analyze.txt"
        with open(dict_path, "w", encoding="utf-8") as out_file:
            pprint.pprint(graph_dict, out_file, indent=4, sort_dicts=False)

    draw_pyan_graph(items.def_items, items.use_dict, output_dict)
    draw_plantuml_graph(items.use_dict, output_dict)


def main():
    parser = argparse.ArgumentParser(description="Thread graph generator")
    parser.add_argument("-f", "--files", nargs="+", default=[], help="Files to analyze")
    parser.add_argument("--outsvgfile", action="store", required=True, help="Path to output SVG file")
    parser.add_argument("--outdotfile", action="store", required=False, help="Path to output DOT file")
    parser.add_argument("--outhtmlfile", action="store", required=False, help="Path to output HTML file")
    parser.add_argument("--outseqdiag", action="store", required=False, help="Path to output PlantUml sequence diagram")
    parser.add_argument(
        "--outseqsvg", action="store", required=False, help="Path to output PlantUml sequence diagram as SVG"
    )
    parser.add_argument(
        "-ddd",
        "--dumpdebugdata",
        action="store_true",
        default=False,
        help="Dump various debug data like intermediate structures and graphs",
    )

    args = parser.parse_args()

    # logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)

    files_list = args.files
    _LOGGER.info("parsing files: %s", files_list)

    output_dict = {
        "outdotfile": args.outdotfile,
        "outsvgfile": args.outsvgfile,
        "outhtmlfile": args.outhtmlfile,
        "outseqdiag": args.outseqdiag,
        "outseqsvg": args.outseqsvg,
    }
    analyze_code(files_list, output_dict, args.dumpdebugdata)

    _LOGGER.info("done")
    return 0


## ============================= main section ===================================


if __name__ == "__main__":
    EXIT_CODE = main()
    sys.exit(EXIT_CODE)
