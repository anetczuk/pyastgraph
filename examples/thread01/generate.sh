#!/bin/bash

set -eu

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

SRC_DIR="$SCRIPT_DIR/../../src"

OUT_DIR="$SCRIPT_DIR/out"

FILES="$SCRIPT_DIR/*.py"


mkdir -p "${OUT_DIR}"


echo "passing files: ${FILES}"

cd $SRC_DIR

python3 -m astgraph -f $FILES \
                    --outsvgfile "$OUT_DIR/graph.svg" \
                    --outdotfile "$OUT_DIR/graph.dot.txt" \
                    --outseqdiag "$OUT_DIR/graph.plantuml" \
                    --outseqsvg "$OUT_DIR/graph.plantuml.svg" \
                    $@

convert -strip -density 80 "$OUT_DIR/graph.svg" "$OUT_DIR/graph.png"


python3 -m astgraph -f $FILES \
                    --filterup '.*Runner.execute.*' \
                    --filterdown '.*Runner.execute.*' \
                    --outsvgfile "$OUT_DIR/graph_filtered.svg" \
                    --outdotfile "$OUT_DIR/graph_filtered.dot.txt" \
                    $@
convert -strip -density 150 "$OUT_DIR/graph_filtered.svg" "$OUT_DIR/graph_filtered.png"
