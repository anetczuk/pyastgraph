#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import os
import unittest

from testastgraph.sample import get_data_root_path

from astgraph.main import analyze_files, process_files
from astgraph.graphtheory import flatten_to_list


class MainTest(unittest.TestCase):
    def test_process_files(self):
        data_root_path = get_data_root_path()
        files_list = []
        files_list.append(os.path.join(data_root_path, "code", "simple_runner.py"))

        process_files(files_list, None, {})

    def test_analyze_data(self):
        data_root_path = get_data_root_path()
        files_list = []
        files_list.append(os.path.join(data_root_path, "code", "simple_runner.py"))

        analyze_data = analyze_files(files_list, None)

        filtered_defs = analyze_data[0]
        filtered_uses = flatten_to_list(analyze_data[1])

        names_defs = [item.get_name() for item in filtered_defs]
        names_uses = [item.get_name() for item in filtered_uses]

        names_defs.sort()
        names_uses.sort()

        self.assertEqual(
            names_defs, ["Runner", "STATIC_FIELD", "__init__", "execute", "instance_field", "main", "simple_runner"]
        )
        self.assertEqual(names_uses, ["STATIC_FIELD", "__init__", "execute", "instance_field", "main", "simple_runner"])

    def test_analyze_data_filter(self):
        data_root_path = get_data_root_path()
        files_list = []
        files_list.append(os.path.join(data_root_path, "code", "simple_runner.py"))
        filters = {"filterdown": [".*Runner.execute.*"]}

        analyze_data = analyze_files(files_list, filters)

        filtered_defs = analyze_data[0]
        filtered_uses = flatten_to_list(analyze_data[1])

        names_defs = [item.get_name() for item in filtered_defs]
        names_uses = [item.get_name() for item in filtered_uses]

        names_defs.sort()
        names_uses.sort()

        # self.assertEqual(names_defs, ['Runner', 'execute', 'simple_runner'])
        self.assertEqual(names_uses, ["STATIC_FIELD", "execute", "instance_field"])
