#!/bin/bash

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the required dependencies
pip install -r lib_requirements.txt

# Run the main Python script
python Allen_main.py

# Deactivate the virtual environment
deactivate

