#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


# run tests in venv (it verifies required packages)
$SCRIPT_DIR/tools/installvenv.sh --no-prompt
$SCRIPT_DIR/venv/runtests.py

$SCRIPT_DIR/doc/generate-doc.sh

$SCRIPT_DIR/tools/mdpreproc.py $SCRIPT_DIR/README.md

$SCRIPT_DIR/examples/generate-all.sh

$SCRIPT_DIR/tools/checkall.sh


echo "processing completed"
