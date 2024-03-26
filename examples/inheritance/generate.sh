#!/bin/bash

set -eu

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


SRC_DIR="$SCRIPT_DIR/../../src"

OUT_DIR="$SCRIPT_DIR/out"

mkdir -p "${OUT_DIR}"


cd $SRC_DIR


FILES="$SCRIPT_DIR/inheritance.py"
python3 -m astgraph -f $FILES \
                    --outsvgfile "$OUT_DIR/inheritance.svg" \
                    --outdotfile "$OUT_DIR/inheritance.dot.txt" \
                    --outseqdiag "$OUT_DIR/inheritance.plantuml" \
                    --outseqsvg "$OUT_DIR/inheritance.plantuml.svg" \
                    $@
convert -strip -density 150 "$OUT_DIR/inheritance.svg" "$OUT_DIR/inheritance.png"


FILES="$SRC_DIR/testastgraph/sample/code/inherit/inherit01.py"
python3 -m astgraph -f $FILES \
                    --outsvgfile "$OUT_DIR/inherit01.svg" \
                    --outdotfile "$OUT_DIR/inherit01.dot.txt" \
                    --outseqdiag "$OUT_DIR/inherit01.plantuml" \
                    --outseqsvg "$OUT_DIR/inherit01.plantuml.svg" \
                    $@
convert -strip -density 150 "$OUT_DIR/inherit01.svg" "$OUT_DIR/inherit01.png"


FILES="$SRC_DIR/testastgraph/sample/code/inherit/inherit02.py"
python3 -m astgraph -f $FILES \
                    --outsvgfile "$OUT_DIR/inherit02.svg" \
                    --outdotfile "$OUT_DIR/inherit02.dot.txt" \
                    --outseqdiag "$OUT_DIR/inherit02.plantuml" \
                    --outseqsvg "$OUT_DIR/inherit02.plantuml.svg" \
                    $@
convert -strip -density 150 "$OUT_DIR/inherit02.svg" "$OUT_DIR/inherit02.png"


FILES="$SRC_DIR/testastgraph/sample/code/inherit/inherit03.py"
python3 -m astgraph -f $FILES \
                    --outsvgfile "$OUT_DIR/inherit03.svg" \
                    --outdotfile "$OUT_DIR/inherit03.dot.txt" \
                    --outseqdiag "$OUT_DIR/inherit03.plantuml" \
                    --outseqsvg "$OUT_DIR/inherit03.plantuml.svg" \
                    $@
convert -strip -density 150 "$OUT_DIR/inherit03.svg" "$OUT_DIR/inherit03.png"


FILES="$SRC_DIR/testastgraph/sample/code/inherit/override01.py"
python3 -m astgraph -f $FILES \
                    --outsvgfile "$OUT_DIR/override01.svg" \
                    --outdotfile "$OUT_DIR/override01.dot.txt" \
                    --outseqdiag "$OUT_DIR/override01.plantuml" \
                    --outseqsvg "$OUT_DIR/override01.plantuml.svg" \
                    $@
convert -strip -density 150 "$OUT_DIR/override01.svg" "$OUT_DIR/override01.png"


echo "completed"
