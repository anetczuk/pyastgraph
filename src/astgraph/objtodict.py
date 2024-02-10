#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import logging
from typing import Iterable


_LOGGER = logging.getLogger(__name__)


## =====================================================


class ObjRepr:
    def __init__(self):
        self._visited = set()
        self.skip_meta_data = False
        self.ignore_fields = []

    def repr_obj(self, obj, skip_meta_data=False, ignore_fields=None):
        self.skip_meta_data = skip_meta_data
        if ignore_fields:
            self.ignore_fields = ignore_fields
        self._visited.clear()
        return self._visit(obj)

    def _visit(self, obj):
        obj_id = id(obj)
        if obj_id in self._visited:
            # print("visited:", type(next_obj), next_obj)
            return obj
        self._visited.add(obj_id)

        if isinstance(obj, dict):
            ret_dict = {}
            for key, data in obj.items():
                if key in self.ignore_fields:
                    ret_dict[key] = "<ignored>"
                    continue
                ret_dict[key] = self._visit(data)
            return ret_dict

        if hasattr(obj, "__dict__"):
            if self.skip_meta_data:
                ret_dict = {}
            else:
                ret_dict = {"___type___": type(obj).__name__, "___id___": hex(id(obj))}
            for key, data in obj.__dict__.items():
                if key in self.ignore_fields:
                    ret_dict[key] = "<ignored>"
                    continue
                ret_dict[key] = self._visit(data)
            return ret_dict

        if hasattr(obj, "__slots__"):
            if self.skip_meta_data:
                ret_dict = {}
            else:
                ret_dict = {"___type___": type(obj).__name__, "___id___": hex(id(obj))}
            for key in obj.__slots__:
                if key in self.ignore_fields:
                    ret_dict[key] = "<ignored>"
                    continue
                data = getattr(obj, key)
                ret_dict[key] = self._visit(data)
            return ret_dict

        if isinstance(obj, str):
            return obj

        if isinstance(obj, Iterable):
            ret_list = []
            for data in obj:
                ret_list.append(self._visit(data))
            return ret_list

        return obj


def obj_to_dict(obj, skip_meta_data=False, ignore_fields=None):
    repr_obj = ObjRepr()
    return repr_obj.repr_obj(obj, skip_meta_data=skip_meta_data, ignore_fields=ignore_fields)
