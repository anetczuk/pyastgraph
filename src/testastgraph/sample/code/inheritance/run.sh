#!/bin/bash

set -eu

##
## Execute module to ensure code is valid.
##


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


python3 $SCRIPT_DIR/inherit01.py

python3 $SCRIPT_DIR/inherit02.py

python3 $SCRIPT_DIR/inherit03.py


echo "all valid"
