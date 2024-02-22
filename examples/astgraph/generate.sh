#!/bin/bash

set -eu

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

SRC_DIR="$SCRIPT_DIR/../../src"

OUT_DIR="$SCRIPT_DIR/out"

mkdir -p "${OUT_DIR}"


cd $SRC_DIR


FILES=$(find $SRC_DIR/astgraph -type f -name "*.py")
echo "passing files: ${FILES}"

python3 -m astgraph -f $FILES --outsvgfile "$OUT_DIR/astgraph.svg" --outdotfile "$OUT_DIR/astgraph.dot.txt" $@
convert -strip -density 80 "$OUT_DIR/astgraph.svg" "$OUT_DIR/astgraph.png"
