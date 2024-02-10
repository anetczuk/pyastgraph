#!/bin/bash

set -eu

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

SRC_DIR="$SCRIPT_DIR/../../src"

OUT_DIR="$SCRIPT_DIR/out"

mkdir -p "${OUT_DIR}"


cd $SRC_DIR


FILES="$SCRIPT_DIR/invalid01.py"
echo "passing files: ${FILES}"
python3 -m astgraph -f $FILES --outsvgfile "$OUT_DIR/invalid01.svg" --outdotfile "$OUT_DIR/invalid01.dot.txt" $@
