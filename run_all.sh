#!/bin/bash
# Run the Persona-Driven Document Intelligence on all collections

echo "========================================================"
echo "    Persona-Driven Document Intelligence Processor"
echo "            Processing All Collections"
echo "========================================================"
echo

# Get directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Create models directory if it doesn't exist
mkdir -p models

# Process all collections with the main script
echo "Processing all collections..."
python main.py --base_dir .
echo

echo "All collections processed successfully!"
echo "========================================================"
