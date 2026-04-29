#!/bin/bash

# --- Input Parameter Handling ---

# 1. Check for the required first argument (the input list/range for -i)
if [ -z "$1" ]; then
    echo "Error: Missing required arguments: type and job list/range."
    echo "Usage:   ./post_runner.sh [TASK_TYPE] \"[LIST_OF_RANGE]\"  "
    echo "Example: ./post_runner.sh cleat_drum  \"142872, 142879:142894\"  "
    exit 1
fi

# 2. Set the TASK_TYPE variable
TASK_TYPE="$1"

# Store the parameters in descriptive variables
INPUT_LIST="$2"

# 3. Validate the TASK_TYPE against allowed options
VALID_TYPES="braking freerolling cornering cleat_drum"
if [[ ! " $VALID_TYPES " =~ " $TASK_TYPE " ]]; then
    echo "Error: Invalid task type '$TASK_TYPE' provided."
    echo "Valid options are: braking, freerolling, cornering, cleat_drum."
    exit 1
fi

# --- Virtual Environment Setup ---

# 4. Define the exact path to your virtual environment's activation script
VENV_ACTIVATE_SCRIPT="/home/ZhangHui/software/venv/env_common/bin/activate"

# 5. Check if the activation script exists
if [ ! -f "$VENV_ACTIVATE_SCRIPT" ]; then
    echo "Error: Virtual environment activation script not found at $VENV_ACTIVATE_SCRIPT"
    exit 1
fi

# 6. Activate the virtual environment
echo "Activating environment..."
source "$VENV_ACTIVATE_SCRIPT"

# --- Script Execution ---

# 7. Execute the Python script
# "$INPUT_LIST" holds the input argument for -i.
# "$TASK_TYPE" holds the input argument for -t (either the default or the user-specified value).
echo "Running Python script with arguments:"
echo "  -t: $TASK_TYPE"
echo "  -i: [$INPUT_LIST]"

python main_abaqus_post.py -i "[$INPUT_LIST]" -o "." -t "$TASK_TYPE"

# 8. Deactivate the environment (Good practice to clean up the shell session)
deactivate

echo "Execution complete."
