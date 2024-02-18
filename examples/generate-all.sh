#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


$SCRIPT_DIR/simple/generate.sh

$SCRIPT_DIR/multifile01/generate.sh
