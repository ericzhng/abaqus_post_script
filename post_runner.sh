#!/bin/bash

# 1. Check for required argument (the input list/range for -i)
if [ -z "$1" ]; then
    echo "Error: Missing required argument for the input list (-i)."
    echo "Usage: ./run_post_processing.sh \"[LIST_OR_RANGE]\""
    echo "Example: ./run_post_processing.sh \"[142872, 142879:142894]\""
    exit 1
fi

# 2. Define the exact path to your virtual environment's activation script
VENV_ACTIVATE_SCRIPT="/home/ZhangHui/software/venv/env_common/bin/activate"

# 3. Check if the activation script exists
if [ ! -f "$VENV_ACTIVATE_SCRIPT" ]; then
    echo "Error: Virtual environment activation script not found at $VENV_ACTIVATE_SCRIPT"
    exit 1
fi

# 4. Activate the virtual environment
echo "Activating environment..."
source "$VENV_ACTIVATE_SCRIPT"

# 5. Execute the Python script
# "$1" holds the input argument passed to this bash script.
# We keep it quoted to correctly handle the brackets and commas.
echo "Running Python script with -i argument: $1"
python main_abaqus_post.py -i "[$1]" -o "." -t "Braking"

# 6. Deactivate the environment (Good practice to clean up the shell session)
deactivate

echo "Execution complete."
