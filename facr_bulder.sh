#!/bin/zsh
# facr_bulder.sh
# A script to build facr rules

export base_dir=~/source/repos/facr_builder
export SERVICES=${base_dir}/data/services.yml
export INPUT=./input.txt
export OUTPUT=./output.csv

source ${base_dir}/.venv/bin/activate
python ${base_dir}/src/facr_builder.py $*
deactivate