#!/bin/bash

set -eu

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

SRC_DIR="$SCRIPT_DIR/../../src"

OUT_DIR="$SCRIPT_DIR/out"

mkdir -p "${OUT_DIR}"


## get source of particular commit (prevent permament changes)
COMMIT_SHA="42ce1c3a4ceb0c501a4f38758f51315db6e0fcbd"

TMP_DIR="$SRC_DIR/../tmp/examples"
mkdir -p "$TMP_DIR"
cd "$TMP_DIR"

if [ ! -f "${COMMIT_SHA}.zip" ]; then
    wget https://github.com/anetczuk/pyastgraph/archive/${COMMIT_SHA}.zip
    unzip "${COMMIT_SHA}.zip"
    mv pyastgraph-${COMMIT_SHA} pyastgraph
fi

DATA_DIR="${TMP_DIR}/pyastgraph/src"


cd $SRC_DIR


python3 -m astgraph -d "$DATA_DIR/astgraph" \
                    --showdefs \
                    --outsvgfile "$OUT_DIR/astgraph.svg" \
                    --outdotfile "$OUT_DIR/astgraph.dot.txt" \
                    --outhtmlfile "$OUT_DIR/astgraph.html" \
                    --outseqdiag "$OUT_DIR/astgraph.plantuml" \
                    --outseqsvg "$OUT_DIR/astgraph.plantuml.svg" \
                    $@
convert -strip -density 80 "$OUT_DIR/astgraph.svg" "$OUT_DIR/astgraph.png"


python3 -m astgraph -d "$DATA_DIR/astgraph" \
                    --filterdown '.*TreeParser.*' \
                    --outsvgfile "$OUT_DIR/astgraph_filter_down.svg" \
                    --outdotfile "$OUT_DIR/astgraph_filter_down.dot.txt" \
                    $@
convert -strip -density 150 "$OUT_DIR/astgraph_filter_down.svg" "$OUT_DIR/astgraph_filter_down.png"
