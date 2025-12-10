#!/bin/bash

# --- Input Parameter Handling ---

# 1. Check for the required first argument (the input list/range for -i)
if [ -z "$1" ]; then
    echo "Error: Missing required argument 1: the input list/range for -i."
    echo "Usage: ./post_runner.sh \"[LIST_OF_RANGE]\" [TASK_TYPE]"
    echo "Example 1 (Default: Braking): ./post_runner.sh \"142872, 142879:142894\""
    echo "Example 2 (Specify Type): ./post_runner.sh \"142872, 142879:142894\" Cornering"
    exit 1
fi

# Store the parameters in descriptive variables
INPUT_LIST="$1"

# 2. Set the TASK_TYPE variable
# If $2 is not provided (i.e., it's empty), default to "Braking".
# Otherwise, use the provided argument $2.
TASK_TYPE="${2:-Braking}"

# 3. Validate the TASK_TYPE against allowed options
VALID_TYPES="Braking FreeRolling Cornering"
if [[ ! " $VALID_TYPES " =~ " $TASK_TYPE " ]]; then
    echo "Error: Invalid task type '$TASK_TYPE' provided."
    echo "Valid options are: Braking, FreeRolling, Cornering."
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
echo "  -i: [$INPUT_LIST]"
echo "  -t: $TASK_TYPE (Set as default if 2nd parameter not provided)"

python main_abaqus_post.py -i "[$INPUT_LIST]" -o "." -t "$TASK_TYPE"

# 8. Deactivate the environment (Good practice to clean up the shell session)
deactivate

echo "Execution complete."
