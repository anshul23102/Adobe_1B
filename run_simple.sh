#!/bin/bash
# Run the Persona-Driven Document Intelligence processor
echo "========================================================="
echo "       Persona-Driven Document Intelligence"
echo "========================================================="
echo

# Ensure we're in the correct directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check Python installation
if ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in your PATH"
    echo "Please install Python and try again."
    exit 1
fi

# Run for all collections by default
echo "Processing all collections..."
python main.py --base_dir .

echo
echo "========================================================="
echo "Processing complete! Results saved to each collection directory."
echo "========================================================="
