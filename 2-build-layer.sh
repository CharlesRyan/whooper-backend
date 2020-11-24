#!/bin/bash
set -eo pipefail
rm -rf package
cd function
pip3 install --no-deps --target ../package/python -r requirements.txt
