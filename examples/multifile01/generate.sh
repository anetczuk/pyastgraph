#!/bin/bash

set -eu

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

SRC_DIR="$SCRIPT_DIR/../../src"

OUT_DIR="$SCRIPT_DIR/out"

mkdir -p "${OUT_DIR}"


cd $SRC_DIR


FILES="$SCRIPT_DIR/multi01.py $SCRIPT_DIR/multi02.py"
echo "passing files: ${FILES}"
python3 -m astgraph -f $FILES --outsvgfile "$OUT_DIR/multifile.svg" --outdotfile "$OUT_DIR/multifile.dot.txt" $@
convert -strip -density 150 "$OUT_DIR/multifile.svg" "$OUT_DIR/multifile.png"
