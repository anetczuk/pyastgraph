#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import os
import json
import yaml


SCRIPT_DIR = os.path.dirname(__file__)


def get_data_root_path() -> str:
    return SCRIPT_DIR


def get_data_path(fileName: str) -> str:
    return os.path.join(SCRIPT_DIR, fileName)


def load_json(fileName: str):
    data_path = get_data_path(fileName)
    with open(data_path, encoding="utf-8") as data_file:
        return json.load(data_file)


def load_yaml(fileName: str):
    data_path = get_data_path(fileName)
    with open(data_path, encoding="utf-8") as data_file:
        return yaml.full_load(data_file)
