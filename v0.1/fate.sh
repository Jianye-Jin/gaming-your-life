#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

python gml_cli_v0.2.py --file GML_v0_1.xlsx "$@"
