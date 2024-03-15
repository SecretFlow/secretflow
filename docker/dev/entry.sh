#!/bin/bash

set -ex

cp -r src src_copied
cd src_copied



conda init
source ~/.bashrc
conda create -n build python=3.8 -y
conda activate build

python3 setup.py bdist_wheel --lite

cp dist/* ../src/docker/dev/
