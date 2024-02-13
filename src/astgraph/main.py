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

from astroid.manager import AstroidManager

from astgraph.objtodict import obj_to_dict
from astgraph.treeparser import TreeParser
from astgraph.pyanwrap import draw_graph


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_LOGGER = logging.getLogger(__name__)


def analyze_code(files_list, out_svg_file_path, out_dot_file_path, debug_dump=False):
    files_list = sorted(files_list)
    for index, src_file_path in enumerate(files_list):
        # if debug_dump:
        #     item_out_path = f"{out_svg_file_path}.dot_{index}.txt"
        #     draw_ast_graph(src_file_path, item_out_path)

        mngr = AstroidManager()
        astroid_tree = mngr.ast_from_file(src_file_path)

        repr_tree = astroid_tree.repr_tree()
        _LOGGER.info("astroid representation tree:\n%s", repr_tree)

        if debug_dump:
            graph_dict = obj_to_dict(astroid_tree, skip_meta_data=False)
            dict_path = f"{out_svg_file_path}.astroid_{index}.txt"
            with open(dict_path, "w", encoding="utf-8") as out_file:
                pprint.pprint(graph_dict, out_file, indent=4)

        analyzer = TreeParser()
        analyzer.analyze(astroid_tree)
        items = analyzer.items

        if debug_dump:
            graph_dict = obj_to_dict(items, skip_meta_data=False)
            dict_path = f"{out_svg_file_path}.analyze_{index}.txt"
            with open(dict_path, "w", encoding="utf-8") as out_file:
                pprint.pprint(graph_dict, out_file, indent=4, sort_dicts=False)

        draw_graph(items.def_items, items.use_dict, out_svg_file_path, out_dot_file_path)


def main():
    parser = argparse.ArgumentParser(description="Thread graph generator")
    parser.add_argument("-f", "--files", nargs="+", default=[], help="Files to analyze")
    parser.add_argument("--outsvgfile", action="store", required=True, help="Path to output SVG file")
    parser.add_argument("--outdotfile", action="store", required=False, help="Path to output DOT file")
    parser.add_argument(
        "-ddd",
        "--dumpdebugdata",
        action="store_true",
        default=False,
        help="Dump varius debug data like intermediate structures and graphs",
    )

    args = parser.parse_args()

    # logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)

    files_list = args.files
    _LOGGER.info("parsing files: %s", files_list)

    analyze_code(files_list, args.outsvgfile, args.outdotfile, args.dumpdebugdata)

    _LOGGER.info("done")
    return 0


## ============================= main section ===================================


if __name__ == "__main__":
    EXIT_CODE = main()
    sys.exit(EXIT_CODE)
