addpath(genpath('C:\Users\ZhangHui\Documents\1-code\ericlib\src'));
addpath(genpath('C:\Users\ZhangHui\Desktop\Projects\matlab_spec_compare\src'));
clear; clc;

specName = 'FC483Q';
rawDir = "C:\Users\ZhangHui\Documents\1-code\VOE-Abaqus-Post\output\FC483Q";

nomFZ = 7563;
loadratios = [0.5, 1.0, 1.5];

% specify template tydex file
rootDir = "C:\Users\ZhangHui\Documents\1-code\VOE-Abaqus-Post\output\FC483Q-Report";
tdxFile = fullfile(rootDir, 'A-31633_Cleat_20x20-0deg__90kph_3782N_260kPa.tdx');

%========================
% no changes afterwards
%========================

tydexDir = fullfile(rawDir, 'tdx');
if ~exist(tydexDir, 'dir'); mkdir(tydexDir); end

saveDir = fullfile(rawDir, 'plots');

fprintf('Processing Cleat data...\n');

% read reference tydex file
tdxInfo = read_tydex(tdxFile);

% plot options
options = struct();
options.removeDc = false;
options.alignTime = true;
options.plotPsd = true;
options.useCompact = true;
options.psdMaxFreq = 300;
options.fontSize = 11;
options.resolution = 300;

plotFields = {'fz', 'fx'};

dirPat = dir(fullfile(rawDir, '*.json'));

R_drum = 1.0; % m

for k = 3:3 % 1:numel(dirPat)
    fprintf('\n[%d/%d] Reading JSON file: %s\n', k, numel(dirPat), dirPat(k).name);

    jsonData = read_json(fullfile(dirPat(k).folder, dirPat(k).name));

    % update measdata: assume consistent units
    runtime = jsonData.runtime / 1.0E3;
    fx = -jsonData.rim_handle_RF1_ANTIALIASING;
    fyc = jsonData.rim_handle_RF2_ANTIALIASING;
    fzc = jsonData.rim_handle_RF3_ANTIALIASING;
    travdisc = jsonData.drum_spindle_connector_CVR1 * R_drum .* jsonData.runtime;
    % omega unit: rad/ms; R_drum unit: m; -> m/s
    trajvelw = jsonData.drum_spindle_connector_CVR1 * 1E3 * R_drum * 3.6;
    whrotspd = -jsonData.rim_spindle_connector_CVR1_ANTIALIASING * 1E3 * 60 / (pi * 2.0);

    [idx_range, mean_value_idx, flag_early_impact] = cut_signal_range(runtime, fzc, trajvelw);

    fz_mean = mean(fzc(mean_value_idx));
    fx_mean = mean(fx(mean_value_idx));
    fy_mean = mean(fyc(mean_value_idx));
    id_start = find(idx_range, 1);

    % obtain load, velocity
    speed_mean = mean(trajvelw(mean_value_idx));
    [~, index] = min(abs(nomFZ * loadratios - fz_mean));
    FZ_nominal = nomFZ * loadratios(index);

    % print precentage of change
    perc_change = abs(fz_mean - FZ_nominal) / FZ_nominal * 100;

    if perc_change > 5
        warning('  -> FZ percentage of change exceeds 5%.');
    end

    fprintf('  -> Evaluated nominal conditions: FZ = %.0f N, Speed = %.0f kph\n', FZ_nominal, speed_mean);

    % update common sections
    % tdxInfo.header.measid.value = specName;
    tdxInfo.header.supplier.value = 'Bridgestone';
    tdxInfo.header.date.value = char(datetime('now', 'Format', 'd-MMM-yyyy'));
    tdxInfo.header.clcktime.value = char(datetime('now', 'Format', 'HH:mm:ss'));
    tdxInfo.comments = ['Converted on ' char(datetime("now")) '.'];

    % update specific constants
    tdxInfo.constants.fzc.value = FZ_nominal;
    tdxInfo.constants.longvel.value = speed_mean / 3.6;

    if flag_early_impact
        warning('  -> Early impact before velocity stabilization, show whole signal, no saving cleat tydex.');
        id_start = 1;
        idx_range = 1:numel(runtime);
    end

    tdxInfo.measdata.runtime = runtime(idx_range) - runtime(id_start);
    tdxInfo.measdata.fx = fx(idx_range) - fx_mean;
    tdxInfo.measdata.fyc = fyc(idx_range) - fy_mean;
    tdxInfo.measdata.fzc = fzc(idx_range) - fz_mean;
    tdxInfo.measdata.travdisc = travdisc(idx_range) - travdisc(id_start);
    tdxInfo.measdata.trajvelw = trajvelw(idx_range);
    tdxInfo.measdata.whrotspd = whrotspd(idx_range);

    % need to determine the cleat angle from FY magnitude
    maxFX = max(abs(tdxInfo.measdata.fx));
    maxFY = max(abs(tdxInfo.measdata.fyc));
    maxFZ = max(abs(tdxInfo.measdata.fzc));

    if maxFY > maxFX * 0.15
        cleatAngle_specify = 45;
        cleat_type = 'oblique';
        fprintf('  -> Signal detected as oblique cleat (45 deg)\n');
    else
        cleatAngle_specify = 0;
        cleat_type = 'transverse';
        fprintf('  -> Signal detected as transverse cleat (0 deg)\n');
    end

    fname = sprintf("Cleat_20x20-%s_%.0fkph_%.0fN.tdx", cleat_type, speed_mean, FZ_nominal);
    fprintf('  -> Saving TDX output: %s\n', fname);

    write_tydex(fullfile(tydexDir, fname), tdxInfo);
    outdata = read_tydex(fullfile(tydexDir, fname));
    cleatSignals(1) = extract_cleat_signal(outdata);

    if flag_early_impact
        % remove tydex file
        delete(fullfile(tydexDir, fname));
    end

    strTitle = sprintf('%s, FZ: %.0fN, VX: %.0fkph', cleat_type, FZ_nominal, speed_mean);
    filename = sprintf('%s_%.0fN_%.0fkph_%s_cleat.png', specName, FZ_nominal, speed_mean, cleat_type);

    legendLabels = {'Vulcan'};
    fprintf('  -> Generating and saving plot: %s\n', filename);
    plot_cleat_signals(cleatSignals, legendLabels, plotFields, options, saveDir, filename, strTitle);

    fprintf('  -> Finished processing file %d of %d.\n', k, numel(dirPat));
end
