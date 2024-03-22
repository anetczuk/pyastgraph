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

from glob import glob
import re
import pprint

from astgraph.objtodict import obj_to_dict
from astgraph.treeparser import TreeParser, DefItem
from astgraph.pyanwrap import draw_use_graph as draw_pyan_graph
from astgraph.plantuml import draw_graph as draw_plantuml_graph
from astgraph.graphtheory import filter_down, Filter, join_graph, filter_up


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_LOGGER = logging.getLogger(__name__)


def process_files(files_list, filters, output_dict, debug_dump=False):
    data_dump_path = None
    if debug_dump:
        out_svg_file_path = output_dict["outsvgfile"]
        data_dump_path = f"{out_svg_file_path}.analyze.txt"

    analyze_data = analyze_files(files_list, filters, data_dump_path)

    filtered_uses = analyze_data[1]
    draw_pyan_graph(filtered_uses, output_dict)
    draw_plantuml_graph(filtered_uses, output_dict)

    # filtered_defs = analyze_data[0]
    # filtered_uses = analyze_data[1]
    # draw_pyan_graph(filtered_uses, output_dict)
    # draw_pyan_graph(filtered_defs, filtered_uses, output_dict)
    # draw_plantuml_graph(filtered_uses, output_dict)


def analyze_files(files_list, filters, data_dump_path=None):
    if filters is None:
        filters = {}

    analyzer = TreeParser()
    analyzer.analyze_files(files_list)
    items = analyzer.items

    if data_dump_path:
        graph_dict = obj_to_dict(items, skip_meta_data=False)
        with open(data_dump_path, "w", encoding="utf-8") as out_file:
            pprint.pprint(graph_dict, out_file, indent=4, sort_dicts=False)

    filter_down_list = filters.get("filterdown", [])
    filter_up_list = filters.get("filterup", [])

    filtered_defs = items.get_def_dict()
    filtered_uses = {}

    if filter_down_list or filter_up_list:
        if filter_down_list:
            filter_patterns = [re.compile(item) for item in filter_down_list]
            filter_obj = DefItemFilter(filter_patterns)
            down_uses = filter_down(items.use_dict, filter_obj)
            join_graph(filtered_uses, down_uses)

            # defs_dict = items.get_def_dict()
            # print("xxxxxxxxxxxx1:", defs_dict)
            # filtered_defs = filter_updown(defs_dict, filter_obj)
            # print("xxxxxxxxxxxx2:", filtered_defs)
            # filtered_defs = flatten_to_list(filtered_defs)
            # print("xxxxxxxxxxxx3:", filtered_defs)

        if filter_up_list:
            filter_patterns = [re.compile(item) for item in filter_up_list]
            filter_obj = DefItemFilter(filter_patterns)
            up_uses = filter_up(items.use_dict, filter_obj)
            join_graph(filtered_uses, up_uses)

    else:
        filtered_uses = items.use_dict

    return (filtered_defs, filtered_uses)


class DefItemFilter(Filter):
    def is_matching(self, item: DefItem):
        name = item.get_full_name()
        return self._is_matching(name)


# def filter_items(items_list, regex_list):
#     if not items_list:
#         return items_list
#     if not regex_list:
#         return items_list
#
#     ret_list = []
#     pattern_list = [re.compile(item) for item in regex_list]
#     for item in items_list:
#         is_excluded = False
#         for pattern in pattern_list:
#             if pattern.match(item):
#                 is_excluded = True
#                 break
#         if is_excluded is False:
#             ret_list.append(item)
#
#     return ret_list


# ext - with dot if needed
def find_files(search_dir, ext):
    ret_list = []
    for filename in glob(f"{search_dir}/**/*{ext}", recursive=True):
        ret_list.append(filename)
    return ret_list


def main():
    parser = argparse.ArgumentParser(description="Thread graph generator")
    parser.add_argument("-f", "--files", nargs="+", default=[], help="Files to analyze")
    parser.add_argument("-d", "--dir", action="store", help="Path to directory to search .py files")
    parser.add_argument(
        "--filterdown",
        metavar="N",
        type=str,
        nargs="+",
        help="Space separated list of regex strings applied on found items to be included in diagram"
        " (otherwise items will be excluded)",
    )
    parser.add_argument(
        "--filterup",
        metavar="N",
        type=str,
        nargs="+",
        help="Space separated list of regex strings applied on found items to be included in diagram"
        " (otherwise items will be excluded)",
    )
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

    filters = {"filterdown": args.filterdown, "filterup": args.filterup}

    files_list = find_files(args.dir, ".py")
    if args.files:
        files_list.extend(args.files)

    _LOGGER.info("parsing files: %s", files_list)

    output_dict = {
        "outdotfile": args.outdotfile,
        "outsvgfile": args.outsvgfile,
        "outhtmlfile": args.outhtmlfile,
        "outseqdiag": args.outseqdiag,
        "outseqsvg": args.outseqsvg,
    }
    process_files(files_list, filters, output_dict, args.dumpdebugdata)

    _LOGGER.info("done")
    return 0


## ============================= main section ===================================


if __name__ == "__main__":
    EXIT_CODE = main()
    sys.exit(EXIT_CODE)
