#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the GNU GENERAL PUBLIC LICENSE, Version 2, June 1991, found in the
# LICENSE file in the root directory of this source tree.
#

import os
import logging
import itertools
import math
import hashlib
from collections import namedtuple
import tempfile
import shutil

from enum import Enum, unique

from typing import List, Dict

from showgraph.io import write_file, read_list
from astgraph.treeparser import DefItem, DefItemType
from astgraph.graphtheory import get_root_items, visit_graph


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_LOGGER = logging.getLogger(__name__)


BG_COLORS_PATH = os.path.join(SCRIPT_DIR, "plantuml_bg_colors.txt")
BG_COLORS_LIST = read_list(BG_COLORS_PATH)


# =======================================================


@unique
class NoteType(Enum):
    """Type of note."""

    INFO = "INFO"
    ERROR = "ERROR"


##
class NotesContainer:
    def __init__(self):
        self._notes_lines = []
        self.bg_color: str = None

    ## list interface
    def __len__(self):
        return len(self._notes_lines)

    ## list interface
    def __getitem__(self, item):
        return self._notes_lines[item]

    ## list interface
    def __iter__(self):
        return self._notes_lines.__iter__()


##
class SequenceCall:
    def __init__(self):
        self.parent: SequenceCall = None
        self.caller: str = ""  # actor name
        self.calles: List[str] = []  # actor names
        self.subcalls: List[SequenceCall] = []
        self.label: str = None
        self.label_note = False
        self.notes_data: NotesContainer = None

    def get_receiver(self):
        if self.calles:
            return self.calles[0]
        return None

    def append_subcall(self, subcall):
        subcall.parent = self
        self.subcalls.append(subcall)

    def add_simple_subcall(self, caller_name, calle_name, label):
        call = SequenceCall.create_simple(caller_name, calle_name, label)
        self.append_subcall(call)
        return call

    def add_subcalles(self, caller_name, calle_names, label):
        call = SequenceCall.create_calles(caller_name, calle_names, label)
        self.append_subcall(call)
        return call

    def get_flat_list(self):
        ret_list = []
        ret_list.append(self)
        index = 0
        while index < len(ret_list):
            item = ret_list[index]
            ret_list.extend(item.subcalls)
            index += 1
        return ret_list

    @staticmethod
    def create_simple(caller, calle, label):
        call = SequenceCall()
        call.caller = caller
        if calle:
            call.calles.append(calle)
        call.label = label
        return call

    @staticmethod
    def create_calles(caller, calles, label):
        call = SequenceCall()
        call.caller = caller
        call.calles = calles
        call.label = label
        return call


##
class SequenceCallList:
    def __init__(self, repeats=0):
        self.repeats: int = repeats  # if repeats > 0 then loop
        self.items: List[SequenceCall] = []

    def add_simple_call(self, caller, calle, label):
        call = SequenceCall.create_simple(caller, calle, label)
        self.items.append(call)
        return call

    def add_calles(self, caller, calles, label):
        call = SequenceCall.create_calles(caller, calles, label)
        self.items.append(call)
        return call


ActorData = namedtuple("ActorData", ["name", "label", "bgcolor"])


##
class SequenceGraph:
    def __init__(self):
        self.params = {}
        self.actors_list: List[ActorData] = []
        self.loops: List[SequenceCallList] = []

    def add_actor(self, name, label=None, bgcolor=None):
        self.actors_list.append(ActorData(name, label, bgcolor))

    def append_loop(self, loop):
        self.loops.append(loop)

    def get_actors(self):
        return self.actors_list

    def get_all_calls(self) -> List[SequenceCall]:
        calls_list = []
        for loop in self.loops:
            calls_list.extend(loop.items)
        return calls_list

    def get_all_calls_flat(self) -> List[SequenceCall]:
        loop_calls = self.get_all_calls()
        calls_list: List[SequenceCall] = []
        for item in loop_calls:
            items_list = item.get_flat_list()
            calls_list.extend(items_list)
        return calls_list

    def get_loops(self) -> List[SequenceCallList]:
        return self.loops


# =======================================================


##
class SequenceDiagramGenerator:
    def __init__(self, seq_diagram: SequenceGraph):
        self.seq_diagram: SequenceGraph = seq_diagram

        self.name_dict: Dict[str, str] = {}
        self.params_dict = self.seq_diagram.params
        if self.params_dict is None:
            self.params_dict = {}

    def generate(self, out_path):
        # if self.seq_diagram.empty():
        #     self._write_empty(out_path)
        #     return

        content = """\
@startuml

skinparam backgroundColor #FEFEFE

"""

        ## add actors
        actors_order: List[ActorData] = calculate_actors_optimized_order(self.seq_diagram)
        if actors_order:
            # actor_data: ActorData
            for actor_data in actors_order:
                if actor_data is None:
                    continue
                actor_name: str = actor_data.name

                item_id = self._get_item_id(actor_name)
                item_label = actor_data.label

                actor_bg_color = actor_data.bgcolor
                if actor_bg_color is None and BG_COLORS_LIST:
                    ## BG_COLORS
                    item_hash = hashlib.sha256(item_id.encode("utf-8")).hexdigest()
                    bg_color_index = int(item_hash, 16) % len(BG_COLORS_LIST)
                    actor_bg_color = BG_COLORS_LIST[bg_color_index]

                participant_label = ""
                if item_label:
                    participant_label = f" [[{item_label}]]"

                if actor_bg_color:
                    content += f"""box #{actor_bg_color}\n"""
                    ## content += f"""'bg color: {bg_color}\n"""
                    content += f"""    participant "{actor_name}" as {item_id}{participant_label}\n"""
                    content += "end box\n"
                else:
                    content += f"""participant "{actor_name}" as {item_id}{participant_label}\n"""

        content += "\n"

        ## add calls
        loops: List[SequenceCallList] = self.seq_diagram.get_loops()
        for seq_loop in loops:
            use_loop = seq_loop.repeats > 1
            indent = ""

            if use_loop:
                content += f"""\nloop {seq_loop.repeats} times\n"""
                indent = "    "

            loop_content = self.generate_loop(seq_loop, indent)

            content += loop_content
            if use_loop:
                content += "end\n"

        content += "\n@enduml\n"

        write_file(out_path, content)

    def generate_loop(self, seq: SequenceCallList, loop_indent):
        content = ""
        group_subs = self.params_dict.get("group_subs", False)

        call_list: List[SequenceCall] = seq.items
        ## call_data: SequenceCall
        for call_data in call_list:
            add_content = self._add_seqcall(call_data, loop_indent, group_subs)
            content += add_content

        return content

    def _add_seqcall(self, call_data: SequenceCall, loop_indent, group_subs):
        content = ""

        receivers = sorted(call_data.calles, reverse=True)

        ## topic url: out/topics/_turtle1_cmd_vel.html
        call_label = call_data.label
        label_note = call_data.label_note
        indent = ""

        if len(receivers) > 1:
            use_subs_group = group_subs
            if use_subs_group:
                ## grouping topic subscribers
                content += f"""{loop_indent}group {call_label}\n"""
                call_label = ""
                indent = "    "

            pub_id = self._get_item_id(call_data.caller)
            for rec in receivers:
                rec_id = self._get_item_id(rec)
                content += self._add_call(
                    pub_id, rec_id, call_label, call_data.notes_data, loop_indent + indent, label_note
                )
                call_label = ""  ## clear label after first item

            if use_subs_group:
                content += f"""{loop_indent}end\n"""

        elif len(receivers) == 1:
            item_indent = loop_indent + indent
            rec = receivers[0]
            pub_id = self._get_item_id(call_data.caller)
            rec_id = self._get_item_id(rec)
            content += self._add_call(pub_id, rec_id, call_label, call_data.notes_data, item_indent, label_note)

            use_activate = True
            # if call_data.parent:
            #     # use activate if call is not nested (in the same class)
            #     parent_receiver = call_data.parent.get_receiver()
            #     use_activate = parent_receiver != call_data.get_receiver()

            if call_data.subcalls:
                if use_activate:
                    content += f"""{item_indent}activate {rec_id}\n"""

                for subcall in call_data.subcalls:
                    add_content = self._add_seqcall(subcall, item_indent + "  ", group_subs)
                    content += add_content

                if use_activate:
                    if pub_id:
                        # returning from nested call causes incorrect results - workaround is to use standard arrow
                        content += f"""{item_indent}{rec_id} --> {pub_id}\n"""
                        # content += f"""{item_indent}return\n"""
                    else:
                        # there is problem with "return" under PlantUML version 1.2018.13
                        # workaround is to use regular arrow
                        content += f"""{item_indent}[-->x {rec_id}\n"""
                    content += f"""{item_indent}deactivate {rec_id}\n\n"""

        else:
            # no receivers
            item_indent = loop_indent + indent
            pub_id = self._get_item_id(call_data.caller)
            content += self._add_call(pub_id, None, call_label, call_data.notes_data, item_indent, label_note)
            # no receivers, so there should be no subcalls
            if len(call_data.subcalls) > 0:
                raise RuntimeError("unexpected number of subcalls")

        return content

    def _add_call(self, pub_id, rec_id, call_label, notes_data, indent, label_note: bool):
        if rec_id:
            arrow_label = ""
            if not label_note:
                arrow_label = f": {call_label}"

            if pub_id:
                content = f"""{indent}{pub_id} o-> {rec_id} {arrow_label}\n"""
            else:
                content = f"""{indent}[-> {rec_id} {arrow_label}\n"""

            if label_note:
                content += f"""{indent}hnote right\n"""
                content += f"""{indent}{call_label}\n"""
                content += f"""{indent}end note\n"""

        else:
            if pub_id:
                content = f"""{indent}hnote right of {pub_id}\n"""
                content += f"""{indent}{call_label}\n"""
                content += f"""{indent}endnote\n"""
                # content = f"""{indent}{pub_id} o->] : {call_label}\n"""
            else:
                raise RuntimeError(
                    f"invalid case: there should be at least one of: publisher id or receiver id in {call_label}"
                )

        if call_label:
            notes_content = self._add_notes(notes_data)
            content += notes_content
        return content

    def _add_notes(self, notes_data: NotesContainer):
        content = ""
        notes_content = convert_notes(notes_data)
        if notes_content is not None:
            bg_color = notes_data.bg_color
            if bg_color is None:
                bg_color = ""
            elif not bg_color.startswith("#"):
                bg_color = "#" + bg_color
            content += f"""\
note left {bg_color}
{notes_content}
end note
"""
        return content

    def _get_item_id(self, item_name):
        if item_name is None:
            return None
        proper = self.name_dict.get(item_name, None)
        if proper is not None:
            return proper
        name = item_name.replace("/", "_")
        self.name_dict[item_name] = name
        return name

    def _write_empty(self, out_path):
        content = """\
@startuml
@enduml
"""
        write_file(out_path, content)


## ========================================================================


def convert_notes(notes_data: NotesContainer):
    if notes_data is None:
        return None
    content_list = []
    for notes_list in notes_data:
        content_line = []
        for note in notes_list:
            note_type = note["type"]
            note_msg = note["msg"]
            if note_type == NoteType.INFO.name:
                content_line.append(note_msg)
            elif note_type == NoteType.ERROR.name:
                msg = format_note_error(note_msg)
                content_line.append(msg)
            else:
                _LOGGER.warning("unhandled note type: %s", note_type)
                content_line.append(note_msg)
        content = " ".join(content_line)
        content_list.append(content)
    return "\n".join(content_list)


def format_note_error(message: str):
    return f"""<b><back:salmon>{message}</back></b>"""


def generate_url(url, label, tooltip):
    return f"""[[{url} {{{tooltip}}} {label}]]"""


def calculate_actors_optimized_order(seq_diagram) -> List[ActorData]:
    graph_actors: List[ActorData] = seq_diagram.get_actors()
    if not graph_actors:
        return None

    all_calls = seq_diagram.get_all_calls()
    distance_dict = {}
    # item: SequenceCall
    for item in all_calls:
        from_actor = item.caller
        to_actors: List[str] = sorted(item.calles, reverse=True)
        if len(to_actors) < 1:
            ## set non-empty label for first subscriber
            continue
        key = tuple(sorted([from_actor, to_actors[0]]))
        distance_dict[key] = len(item.label)

    sorted_actors: List[ActorData] = list(sorted(graph_actors, key=lambda agent: agent.name))

    a_size = len(sorted_actors)

    perm_size = math.factorial(a_size)
    if perm_size > 10000:
        _LOGGER.warning("unable to calculate best order: %s %s %s", len(all_calls), a_size, perm_size)
        return sorted_actors

    _LOGGER.info("calculating best order: %s %s", len(all_calls), a_size)

    sorted_names = [actor.name for actor in sorted_actors]
    sorted_width = calculate_width(sorted_names, distance_dict)
    best_order = sorted_actors
    best_width = sorted_width

    for curr_list in itertools.permutations(sorted_actors, a_size):
        names_list = [actor.name for actor in curr_list]
        curr_width = calculate_width(names_list, distance_dict)
        if curr_width < best_width:
            best_order = list(curr_list)
            best_width = curr_width

    _LOGGER.info("best order: %s %s %s", best_order, best_width, sorted_width)
    return best_order


def calculate_width(names_list: List[str], distance_dict):
    a_size = len(names_list)
    index_distance = [0.0] * a_size
    for i in range(1, a_size):
        curr_actor: str = names_list[i]
        max_dist = 0.0
        for j in range(i - 1, -1, -1):
            prev_actor: str = names_list[j]
            key = tuple(sorted([prev_actor, curr_actor]))
            dist = distance_dict.get(key, 0.0)
            curr_dist = index_distance[j] + dist
            max_dist = max(max_dist, curr_dist)
        index_distance[i] = max_dist
    return index_distance[a_size - 1]


def calculate_combinations(actors_list, index):
    ret_list = []
    list_size = len(actors_list)
    item = actors_list[index]
    reduced_list = actors_list.copy()
    del reduced_list[index]
    for i in range(0, list_size):
        curr_actor = reduced_list.copy()
        curr_actor.insert(i, item)
        ret_list.append(curr_actor)
    return ret_list


def convert_time_index(index_value):
    time_unit = "ms"
    time_value = index_value / 1000000  ## in milliseconds
    if time_value > 10000.0:
        time_value = time_value / 1000
        time_unit = "s"
    return (time_value, time_unit)


def generate_diagram(diagram_data: SequenceGraph, out_path):
    """Generate PlantUML diagram and store to file."""
    genrator = SequenceDiagramGenerator(diagram_data)
    genrator.generate(out_path)


def convert_to_svg(diagram_path, out_svg_path):
    # plantuml converter does not allow to outputting converted diagram to custom file, so
    # following workaround (temporary file) is needed
    with tempfile.NamedTemporaryFile(suffix=".plantuml") as tmpfile:
        try:
            with open(diagram_path, mode="r", encoding="utf-8") as in_file:
                content = in_file.read()
                tmpfile.write(content.encode("utf-8"))
                tmpfile.flush()
        except FileNotFoundError as exc:
            _LOGGER.warning("unable to convert file: %s", exc)
            return

        tmp_diag = tmpfile.name
        command = f"plantuml -tsvg -nometadata {tmp_diag}"
        os.system(command)  # nosec

        split_data = os.path.splitext(tmp_diag)  # split on last dot
        tmp_svg = split_data[0] + ".svg"

        shutil.copyfile(tmp_svg, out_svg_path)
        os.remove(tmp_svg)


# =====================================================


class Converter:
    def __init__(self):
        self.use_dict: Dict[DefItem, List[DefItem]] = None
        self.sequence_graph: SequenceGraph = None
        self.sequence: SequenceCallList = None

    def convert(self, use_dict: Dict[DefItem, List[DefItem]]) -> SequenceGraph:
        self.use_dict = use_dict
        self.sequence_graph = SequenceGraph()

        self.sequence = SequenceCallList(0)
        root_items = get_root_items(self.use_dict)

        # item: DefItem
        for item in root_items:
            nodes_list: List[DefItem] = []
            visit_graph(use_dict, item, nodes_list.append)
            self._convert_root(nodes_list)

        self.sequence_graph.append_loop(self.sequence)
        return self.sequence_graph

    def _convert_root(self, nodes_list: List[DefItem]):
        node_seq_map = {}

        # add first item
        root_item = nodes_list.pop(0)

        use_parent_name = None
        root_seq_call: SequenceCall = None
        if not root_item.is_module():
            use_parent_name = self._get_parent_name(root_item)
            called_name = root_item.get_name()
            root_seq_call = self.sequence.add_simple_call(None, use_parent_name, called_name)
            node_seq_map[root_item] = root_seq_call
        else:
            use_parent_name = root_item.get_name()

        call_list: List[DefItem] = self.use_dict.get(root_item, [])

        # called: DefItem
        for called in call_list:
            called_name = called.get_name()
            called_parent_name = None
            if called.is_method():
                called_parent_name = self._get_parent_name(called)

            if root_seq_call:
                sub_call = root_seq_call.add_simple_subcall(use_parent_name, called_parent_name, called_name)
                node_seq_map[called] = sub_call
            else:
                sub_call = self.sequence.add_simple_call(use_parent_name, called_parent_name, called_name)
                node_seq_map[called] = sub_call

        # add next items
        for node_item in nodes_list:
            parent_call = node_seq_map[node_item]
            use_parent_name = self._get_parent_name(node_item)
            call_list = self.use_dict.get(node_item, [])

            # called: DefItem
            for called in call_list:
                called_name = called.get_name()
                label_note = False
                called_parent_name = self._get_parent_name(called)
                if called.is_field():
                    label_note = True
                    if use_parent_name == called_parent_name:
                        called_parent_name = None
                seq_call: SequenceCall = parent_call.add_simple_subcall(
                    use_parent_name, called_parent_name, called_name
                )
                seq_call.label_note = label_note
                node_seq_map[called] = seq_call

    def _get_parent_name(self, item: DefItem):
        parent = self._get_parent(item)
        if not parent:
            return None
        return parent.get_full_name()

    def _get_parent(self, item: DefItem):
        parent = item.parent
        while parent:
            if parent.type in [DefItemType.MODULE, DefItemType.CLASS]:
                return parent
            parent = parent.parent
        return parent


def draw_graph(use_dict, output_dict=None):
    # import pprint
    # pprint.pprint(use_dict)

    if not output_dict:
        output_dict = {}

    # dump plantuml
    out_seq_diag_path = output_dict.get("outseqdiag")
    out_seq_svg_path = output_dict.get("outseqsvg")

    if not out_seq_diag_path and not out_seq_svg_path:
        return

    converter = Converter()
    sequence_graph = converter.convert(use_dict)

    _LOGGER.info("generating plantuml diagram in file: %s", out_seq_diag_path)
    generate_diagram(sequence_graph, out_seq_diag_path)

    if out_seq_svg_path:
        _LOGGER.info("converting plantuml diagram to file: %s", out_seq_svg_path)
        convert_to_svg(out_seq_diag_path, out_seq_svg_path)
