#!/bin/bash

set -eu

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

SRC_DIR="$SCRIPT_DIR/../../src"

OUT_DIR="$SCRIPT_DIR/out"

mkdir -p "${OUT_DIR}"


cd $SRC_DIR


python3 -m astgraph -d "$SRC_DIR/astgraph" \
                    --outsvgfile "$OUT_DIR/astgraph.svg" \
                    --outdotfile "$OUT_DIR/astgraph.dot.txt" \
                    --outhtmlfile "$OUT_DIR/astgraph.html" \
                    --outseqdiag "$OUT_DIR/astgraph.plantuml" \
                    --outseqsvg "$OUT_DIR/astgraph.plantuml.svg" \
                    $@
convert -strip -density 80 "$OUT_DIR/astgraph.svg" "$OUT_DIR/astgraph.png"


python3 -m astgraph -d "$SRC_DIR/astgraph" \
                    --filterdown '.*TreeParser.*' \
                    --outsvgfile "$OUT_DIR/astgraph_filter_down.svg" \
                    --outdotfile "$OUT_DIR/astgraph_filter_down.dot.txt" \
                    $@
convert -strip -density 150 "$OUT_DIR/astgraph_filter_down.svg" "$OUT_DIR/astgraph_filter_down.png"
