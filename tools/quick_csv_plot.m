%% MATLAB Script to Import and Plot CSV Data
% This script reads data from a CSV file with a header row, extracts the
% first two columns, and creates a simple line plot.

% 1. Configuration
% ---
% NOTE: Ensure 'sample_data.csv' is in the same directory as this script,
% or provide the full file path.
filenames = {'Braking_Sweep_2075N_-0deg.csv'
    'Braking_Sweep_4150N_-0deg.csv'
    'Braking_Sweep_6225N_0deg.csv'
    'Braking_Sweep_6225N_-5deg.csv'};

% ---
figure; % Open a new figure window
hold on;
grid on;
box on;

% 2. Import Data
% ---
% Use readtable to import the data. It automatically detects the header row
% and assigns the column names as variable names.
for k = 1:numel(filenames)
    filename = filenames{k};
    try
        T = readtable(filename);
        disp(['Successfully loaded file: ' filename]);
    catch ME
        disp(['Error loading file: ' filename]);
        disp(['MATLAB Error Message: ' ME.message]);
        return; % Stop execution if file loading fails
    end

    % 3. Extract Columns
    % X-axis data (First Column)
    x_col_name = T.Properties.VariableNames{1};
    x_data = T.(x_col_name);

    % Y-axis data (Second Column)
    y_col_name = T.Properties.VariableNames{2};
    y_data = T.(y_col_name);

    % 4. Plot Data
    plot(x_data, y_data, '-', ... % Plot as a line with circle markers
        'LineWidth', 2, ...
        'MarkerSize', 6, ...
        'MarkerFaceColor', [0.8 0.2 0.2]);
end

% Add labels and title for clarity
title(['Plot of ' y_col_name ' vs ' x_col_name]);
xlabel(x_col_name, 'Interpreter', 'none'); % Use 'none' to handle underscores in names
ylabel(y_col_name, 'Interpreter', 'none');
legend(filenames, Interpreter="none")
