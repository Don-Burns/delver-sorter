#!/bin/bash
# script to update requirements with pip-tools
set -xeuo pipefail
# strip extra index if present, since its a token for codeartifact
pip-compile --no-emit-index-url --upgrade requirements.in
pip-compile --no-emit-index-url --upgrade --output-file=requirements-dev.txt requirements-dev.in
