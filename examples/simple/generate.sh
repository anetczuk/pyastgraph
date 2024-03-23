#!/bin/bash

set -eu

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


SRC_DIR="$SCRIPT_DIR/../../src"

OUT_DIR="$SCRIPT_DIR/out"

mkdir -p "${OUT_DIR}"


cd $SRC_DIR


FILES="$SCRIPT_DIR/single01.py"
echo "passing files: ${FILES}"
python3 -m astgraph -f $FILES \
                    --outsvgfile "$OUT_DIR/single01.svg" \
                    --outdotfile "$OUT_DIR/single01.dot.txt" \
                    --outseqdiag "$OUT_DIR/single01.plantuml" \
                    --outseqsvg "$OUT_DIR/single01.plantuml.svg" \
                    $@
convert -strip -density 150 "$OUT_DIR/single01.svg" "$OUT_DIR/single01.png"
convert -strip -density 150 "$OUT_DIR/single01.plantuml.svg" "$OUT_DIR/single01.plantuml.png"

python3 -m astgraph -f $FILES \
                    --filterdown '.*Runner.execute.*' \
                    --outsvgfile "$OUT_DIR/single01_filter_down.svg" \
                    --outdotfile "$OUT_DIR/single01_filter_down.dot.txt" \
                    $@
convert -strip -density 150 "$OUT_DIR/single01_filter_down.svg" "$OUT_DIR/single01_filter_down.png"

python3 -m astgraph -f $FILES \
                    --filterup '.*Runner.execute.*' \
                    --outsvgfile "$OUT_DIR/single01_filter_up.svg" \
                    --outdotfile "$OUT_DIR/single01_filter_up.dot.txt" \
                    $@
convert -strip -density 150 "$OUT_DIR/single01_filter_up.svg" "$OUT_DIR/single01_filter_up.png"


FILES="$SCRIPT_DIR/chained01.py"
echo "passing files: ${FILES}"
python3 -m astgraph -f $FILES \
                    --outsvgfile "$OUT_DIR/chained01.svg" \
                    --outdotfile "$OUT_DIR/chained01.dot.txt" \
                    --outseqdiag "$OUT_DIR/chained01.plantuml" \
                    --outseqsvg "$OUT_DIR/chained01.plantuml.svg" \
                    $@
convert -strip -density 150 "$OUT_DIR/chained01.svg" "$OUT_DIR/chained01.png"


FILES="$SCRIPT_DIR/invalid01.py"
echo "passing files: ${FILES}"
python3 -m astgraph -f $FILES \
                    --outsvgfile "$OUT_DIR/invalid01.svg" \
                    --outdotfile "$OUT_DIR/invalid01.dot.txt" \
                    --outseqdiag "$OUT_DIR/invalid01.plantuml" \
                    --outseqsvg "$OUT_DIR/invalid01.plantuml.svg" \
                    $@
convert -strip -density 150 "$OUT_DIR/invalid01.svg" "$OUT_DIR/invalid01.png"


## generate miniatures
## 'source' is somehow simillar to C 'include'
echo "generating miniatures"
cd $SCRIPT_DIR
source $SCRIPT_DIR/../../doc/generate_small.sh


echo "completed"
