#!/bin/bash

set -eu

##
## Execute module to ensure code is valid.
##


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


echo -e "\nexecuting inherit01.py"
python3 $SCRIPT_DIR/inherit01.py

echo -e "\nexecuting inherit02.py"
python3 $SCRIPT_DIR/inherit02.py

echo -e "\nexecuting inherit03.py"
python3 $SCRIPT_DIR/inherit03.py

echo -e "\nexecuting override01.py"
python3 $SCRIPT_DIR/override01.py


echo -e "\nall valid"
