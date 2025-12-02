#!/bin/bash
# facr_bulder.sh
# A script to build facr rules

export base_dir=~/source/repos/facr_builder
export SERVICES=${base_dir}/data/services.yml
export HOSTS=/Users/don.bernhardy/OneDrive\ -\ Corpay/Corpay\ Projects/ICD\ Storm\ Migratiion/hosts.txt
export CSVOUT=/Users/don.bernhardy/OneDrive\ -\ Corpay/Corpay\ Projects/ICD\ Storm\ Migratiion/output.csv


# Check if services.yml exists
#if [! -f "${SERVICES}" ]; then
#    echo "Error: services.yml file not found at ${SERVICES}"
#    exit 1
#fi
source ${base_dir}/.venv/bin/activate
python ${base_dir}/src/facr_builder.py $*
deactivate