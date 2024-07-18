#!/bin/bash

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the required dependencies
pip install -r requirements.txt

# Run the main Python script (assuming it's named main.py)
python main.py

# Deactivate the virtual environment
deactivate

