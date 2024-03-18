#!/bin/bash

set -eu

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

SRC_DIR="$SCRIPT_DIR/../../src"

OUT_DIR="$SCRIPT_DIR/out"

mkdir -p "${OUT_DIR}"


cd $SRC_DIR


python3 -m astgraph -d "$SRC_DIR/astgraph" \
                    --outdotfile "$OUT_DIR/astgraph.dot.txt" \
                    --outsvgfile "$OUT_DIR/astgraph.svg" \
                    --outhtmlfile "$OUT_DIR/astgraph.html" \
                    --outseqdiag "$OUT_DIR/astgraph.plantuml" \
                    --outseqsvg "$OUT_DIR/astgraph.plantuml.svg" \
                    $@
convert -strip -density 80 "$OUT_DIR/astgraph.svg" "$OUT_DIR/astgraph.png"
