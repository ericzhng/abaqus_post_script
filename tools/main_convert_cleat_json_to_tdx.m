addpath(genpath('C:\Users\ZhangHui\Documents\1-code\ericlib\src'));
addpath(genpath('C:\Users\ZhangHui\Desktop\Projects\matlab_spec_compare\src'));
clear; clc;

specName = 'FC482Q';
rawDir = "C:\Users\ZhangHui\Documents\1-code\VOE-Abaqus-Post\output\FC482Q";

nomFZ = 7563;
loadratios = [0.5, 1.0, 1.5];

% specify template tydex file
rootDir = "C:\Users\ZhangHui\Documents\1-code\VOE-Abaqus-Post\output\FC483Q";
tdxFile = fullfile(rootDir, 'A-31633_Cleat_20x20-0deg__90kph_3782N_260kPa.tdx');

basefolder = "C:\Users\ZhangHui\Documents\1-code\VOE-Abaqus-Post\output";

%========================
% no changes afterwards
%========================

tdxInfo = read_tydex(tdxFile);

%========================
% muslip
%========================

dirPat = dir(fullfile(rawDir, '*.json'));

% plot options
options = struct();
options.removeDc = false;
options.alignTime = true;
options.plotPsd = true;
options.useCompact = false;
options.psdMaxFreq = 300;
options.fontSize = 11;
options.resolution = 300;

plotFields = {'fz', 'fx', 'fy'};

for k = 4:4 % numel(dirPat)
    jsonData = read_json(fullfile(dirPat(k).folder, dirPat(k).name));

    % obtain load, velocity info
    % omega unit: rad/ms; R_drum unit: m, VX_curr unit: kph
    R_drum = 1.0; % m
    VX_curr = jsonData.drum_spindle_connector_CVR1(end) * 1E3 * R_drum;
    speed_curr = VX_curr * 3.6;
    FZ_curr = mean(jsonData.rim_handle_RF3_ANTIALIASING(end - 10:end));
    [~, index] = min(abs(nomFZ * loadratios - FZ_curr));
    FZ_nominal = nomFZ * loadratios(index);

    % update common sections
    % tdxInfo.header.measid.value = specName;
    tdxInfo.header.supplier.value = 'Bridgestone';
    tdxInfo.header.date.value = char(datetime('now', 'Format', 'd-MMM-yyyy'));
    tdxInfo.header.clcktime.value = char(datetime('now', 'Format', 'HH:mm:ss'));
    tdxInfo.comments = ['Converted on ' char(datetime("now")) '.'];

    % update specific constants
    tdxInfo.constants.fzc.value = FZ_nominal;
    tdxInfo.constants.longvel.value = VX_curr;

    % update measdata: assume consistent units
    runtime = jsonData.runtime / 1.0E3;
    fx = jsonData.rim_handle_RF1_ANTIALIASING;
    fyc = jsonData.rim_handle_RF2_ANTIALIASING;
    fzc = jsonData.rim_handle_RF3_ANTIALIASING;
    travdisc = jsonData.drum_spindle_connector_CVR1 * R_drum .* jsonData.runtime;
    trajvelw = jsonData.drum_spindle_connector_CVR1 * 1E3 * R_drum * 3.6;
    whrotspd = -jsonData.rim_spindle_connector_CVR1_ANTIALIASING * 1E3 * 60 / (pi * 2.0);

    [idx_range, mean_value_idx] = cut_signal_range(runtime, fzc, trajvelw, VX_curr);
    fz_mean = mean(fzc(mean_value_idx));
    fx_mean = mean(fx(mean_value_idx));
    fy_mean = mean(fyc(mean_value_idx));

    id_start = find(idx_range, 1);
    tdxInfo.measdata.runtime = runtime(idx_range) - runtime(id_start);
    tdxInfo.measdata.fx = fx(idx_range) - fx_mean;
    tdxInfo.measdata.fyc = fyc(idx_range) - fy_mean;
    tdxInfo.measdata.fzc = fzc(idx_range) - fz_mean;
    tdxInfo.measdata.travdisc = travdisc(idx_range);
    tdxInfo.measdata.trajvelw = trajvelw(idx_range);
    tdxInfo.measdata.whrotspd = whrotspd(idx_range);

    % need to determine the cleat angle from FY magnitude
    maxFX = max(abs(tdxInfo.measdata.fx));
    maxFY = max(abs(tdxInfo.measdata.fyc));
    maxFZ = max(abs(tdxInfo.measdata.fzc));

    if maxFY > maxFX * 0.3
        cleatAngle_specify = 45;
        fprintf('  Signal detected as oblique cleat\n');
    else
        cleatAngle_specify = 0;
        fprintf('  Signal detected as transverse cleat\n');
    end

    fname = sprintf("Cleat_20x20-%.0fdeg_%.0fkph_%.0fN.tdx", cleatAngle_specify, speed_curr, FZ_nominal);
    write_tydex(fullfile(basefolder, fname), tdxInfo);

    outdata = read_tydex(fullfile(basefolder, fname));

    cleatSignals(1) = extract_cleat_signal(outdata);

    saveDir = fullfile(basefolder, specName, 'output');
    strTitle = sprintf('FZ: %.0fN, VX: %.0fkph', FZ_nominal, speed_curr);
    filename = sprintf('%s_%.0fN_%.0fkph_cleat%.0fdeg.png', specName, FZ_nominal, speed_curr, cleatAngle_specify);

    legendLabels = {'Vulcan'};
    plot_cleat_signals(cleatSignals, legendLabels, plotFields, options, saveDir, filename, strTitle);

    fprintf("(%d/%d): '%s' -> '%s'\n", k, numel(dirPat), dirPat(k).name, fname);
end
