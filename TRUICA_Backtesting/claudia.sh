#!/bin/bash

# Navigate to the directory containing the Python scripts
cd ~/TRUICA_integration/Currencies

# Loop through all .py files in the directory
for file in *.py; do
    echo "Running $file"
    python "$file"
done
