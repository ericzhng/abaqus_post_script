
addpath(genpath('C:\Users\ZhangHui\Documents\1-code\ericlib\src'));
clear; clc;

% specify root directory for ftire raw data
rootDir = "D:\0-data-library\Virtual\GM-FTIRE\ZG719Q";

brakingFolder = fullfile(rootDir, "braking");
corneringFolder = fullfile(rootDir, "cornering");

% use a Vulcan tydex with correct nominal pressure
tdxInfo = fullfile(rootDir, "stiffness", 'A-27348_TotalStiff_Flat_Lat_7563N_270kPa.tdx');

TR_number = 'T23-01204';

%========================
% no changes afterwards
%========================

% for tydex template consistent with ftire
tdxTemp = "..\data\FTire_tydex_template\side_2p7_7fz6_50v.tdx";
tdxData = read_tydex(tdxTemp);

% only for getting basic tire info
tdxInfo = read_tydex(tdxInfo);

%========================
% muslip
%========================

strFilt = 'Braking_*.csv';
dirPat = dir(fullfile(brakingFolder, strFilt));
for k = 1:numel(dirPat)
    % read csv
    Tab = readtable(fullfile(dirPat(k).folder, dirPat(k).name));

    % update common sections
    tdxData.header.measid.value = TR_number;
    tdxData.header.supplier.value = 'Bridgestone';
    tdxData.header.date.value = char(datetime('now', 'Format', 'd-MMM-yyyy'));
    tdxData.header.clcktime.value = char(datetime('now', 'Format', 'HH:mm:ss'));
    tdxData.comments = ['Converted on ' char(datetime("now")) '.'];

    % update constants
    tdxData.constants = update_tydex_constants(tdxData, tdxInfo);

    % update specific constants
    tdxData.constants.fzw.value = Tab.FZ(1);
    tdxData.constants.inclangl.value = Tab.IA(1);
    VX = abs(Tab.VX(1)) * 3.6;
    tdxData.constants.longvel.value = VX;

    % allocate dummy arrays
    nsize = numel(Tab.Slip);

    % update measdata: assume consistent units
    tdxData.measdata.runtime = (1:nsize)' * 0.1;
    tdxData.measdata.fx = Tab.FX;
    tdxData.measdata.fzw = Tab.FZ;
    tdxData.measdata.fyw = Tab.FY;
    tdxData.measdata.mzw = Tab.MZ;
    tdxData.measdata.dstgrwhc = Tab.LR;
    tdxData.measdata.slipangl = Tab.Slip;
    tdxData.measdata.longslip = Tab.Slip;

    % extract conditions
    IP = tdxData.constants.inflpres.value;
    IP_1st = floor(IP);
    IP_2nd = round((IP - IP_1st) * 10);

    FZ = tdxData.constants.fzw.value;
    FZ_1st = floor(FZ / 1000);
    FZ_2nd = floor((FZ - FZ_1st*1000) / 100);

    IA = tdxData.constants.inclangl.value;
    if IA == 0
        strIA = '';
    else
        strIA = sprintf('_%.fcam', IA);
    end

    fname = sprintf("muslip_%dp%d_%dfz%d_%.0fv%s.tdx", IP_1st, IP_2nd, FZ_1st, FZ_2nd, VX, strIA);
    write_tydex(fullfile(brakingFolder, fname), tdxData);

    fprintf("(%d/%d): '%s' -> '%s'\n", k, numel(dirPat), dirPat(k).name, fname);
end

%========================
% side
%========================

strFilt = 'cornering_*.csv';
dirPat = dir(fullfile(corneringFolder, strFilt));
for k = 1:numel(dirPat)
    % read csv
    Tab = readtable(fullfile(dirPat(k).folder, dirPat(k).name));

    % update common sections
    tdxData.header.measid.value = TR_number;
    tdxData.header.supplier.value = 'Bridgestone';
    tdxData.header.date.value = char(datetime('now', 'Format', 'd-MMM-yyyy'));
    tdxData.header.clcktime.value = char(datetime('now', 'Format', 'HH:mm:ss'));
    tdxData.comments = ['Converted on ' char(datetime("now")) '.'];

    % update constants
    tdxData.constants = update_tydex_constants(tdxData, tdxInfo);

    % update specific constants
    tdxData.constants.fzw.value = Tab.FZ(1);
    tdxData.constants.inclangl.value = Tab.IA(1);
    VX = abs(Tab.VX(1)) * 3.6;
    tdxData.constants.longvel.value = VX;

    % allocate dummy arrays
    nsize = numel(Tab.Slip);

    % update measdata: assume consistent units
    tdxData.measdata.runtime = (1:nsize)' * 0.1;
    tdxData.measdata.fx = Tab.FX;
    tdxData.measdata.fzw = Tab.FZ;
    tdxData.measdata.fyw = Tab.FY;
    tdxData.measdata.mzw = Tab.MZ;
    tdxData.measdata.dstgrwhc = Tab.LR;
    tdxData.measdata.slipangl = Tab.Slip;
    tdxData.measdata.longslip = Tab.Slip;

    % extract conditions
    IP = tdxData.constants.inflpres.value;
    IP_1st = floor(IP);
    IP_2nd = round((IP - IP_1st) * 10);

    FZ = tdxData.constants.fzw.value;
    FZ_1st = floor(FZ / 1000);
    FZ_2nd = floor((FZ - FZ_1st*1000) / 100);

    IA = tdxData.constants.inclangl.value;
    if IA == 0
        strIA = '';
    else
        strIA = sprintf('_%.fcam', IA);
    end

    fname = sprintf("side_%dp%d_%dfz%d_%.0fv%s.tdx", IP_1st, IP_2nd, FZ_1st, FZ_2nd, VX, strIA);
    write_tydex(fullfile(corneringFolder, fname), tdxData);

    fprintf("(%d/%d): '%s' -> '%s'\n", k, numel(dirPat), dirPat(k).name, fname);
end
