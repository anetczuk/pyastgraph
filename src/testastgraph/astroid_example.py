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

import astroid
import astypes

from astgraph.treeparser import infer_type


def main():
    code = """\
class ABC3:
    def __init__(self):
        self.field2 = {}

    def get_field(self):
        return self.field2

obj1 = ABC3()
obj1.get_field()
obj1.get_field().get("aaa")
"""

    astroid_node = astroid.parse(code)
    astroid_node.name = "testmod"

    # print(astroid_node.repr_tree())

    class_abc3_node = astroid_node.body[0]
    get_field_node = class_abc3_node.body[1]
    return_node = get_field_node.body[0]
    attr_node = return_node.value  # return attribute node

    node_infer_type = infer_type(attr_node)
    print("return type:", type(node_infer_type))

    obj_call_node = astroid_node.body[2].value
    node_infer_type = infer_type(obj_call_node)
    astype_value = astypes.get_type(obj_call_node)
    print("getter:", type(node_infer_type), astype_value)  # getter return

    obj_call_node = astroid_node.body[3].value
    node_infer_type = infer_type(obj_call_node)
    astype_value = astypes.get_type(obj_call_node)
    print("getter chain:", type(node_infer_type), astype_value)


if __name__ == "__main__":
    main()
