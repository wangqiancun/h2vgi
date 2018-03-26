#!/bin/bash
echo Updating H2VGI...
pip uninstall h2vgi
BASEDIR=$(dirname "$0")
pip install $BASEDIR
echo Done