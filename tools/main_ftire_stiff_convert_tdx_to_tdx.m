
addpath(genpath('C:\Users\ZhangHui\Documents\1-code\ericlib\src'));
clear; clc;

% specify root directory for ftire raw data
rootDir = "D:\0-data-library\Virtual\GM-FTIRE\ZG719Q";

stiffnessFolder = fullfile(rootDir, "stiffness");
% sampleTdx = "A-27348_TotalStiff_Flat_Lat_7563N_270kPa.tdx";

TR_number = 'T23-01204';

%========================
% no changes afterwards
%========================

%========================
% vert and bar
%========================
strFilt = '*_Vert*.tdx';
tdxTemp = "..\data\FTire_tydex_template\vert_2p7.tdx";
tdxTempBar = "..\data\FTire_tydex_template\vert_A_2p7_-6cam.tdx";

dirPat = dir(fullfile(stiffnessFolder, strFilt));
for k = 1:numel(dirPat)
    % read old vulcan data of possibly mismatched format
    tdxDataVulcan = read_tydex(fullfile(dirPat(k).folder, dirPat(k).name));

    if isfield(tdxDataVulcan.constants, 'clt_ori')
        isbar = true;
        tdxData = read_tydex(tdxTempBar);
    else
        isbar = false;
        tdxData = read_tydex(tdxTemp);
    end

    % update common sections
    tdxData.header.measid.value = TR_number;
    tdxData.header.supplier.value = 'Bridgestone';
    tdxData.header.date.value = char(datetime('now', 'Format', 'd-MMM-yyyy'));
    tdxData.header.clcktime.value = char(datetime('now', 'Format', 'HH:mm:ss'));
    tdxData.comments = ['Converted on ' char(datetime("now")) '.'];

    % update constants
    tdxData.constants = update_tydex_constants(tdxData, tdxDataVulcan);

    if isbar
        if str2double(tdxDataVulcan.constants.clt_ori.value) == 90
            tdxData.constants.obsttype.value = 'B';
            strBarType = '_B';
        elseif str2double(tdxDataVulcan.constants.clt_ori.value) == 0
            tdxData.constants.obsttype.value = 'A';
            strBarType = '_A';
        end
    else
        strBarType = '';
    end

    % update measdata: assume consistent units
    tdxData.measdata.runtime = tdxDataVulcan.measdata.runtime;
    tdxData.measdata.fzw = tdxDataVulcan.measdata.fzw;
    tdxData.measdata.fyw = tdxDataVulcan.measdata.fyw;
    tdxData.measdata.fx = tdxDataVulcan.measdata.fxw;
    tdxData.measdata.dstgrwhc = tdxDataVulcan.measdata.dstgrwhc;
    tdxData.measdata.tyredefw = tdxDataVulcan.measdata.tyredefw;

    % extract conditions
    IP = tdxData.constants.inflpres.value;
    IP_1st = floor(IP);
    IP_2nd = round((IP - IP_1st) * 10);

    IA = str2double(tdxData.constants.inclangl.value);
    if IA == 0
        strIA = '';
    else
        strIA = sprintf('_%.fcam', IA);
    end

    fname = sprintf("vert%s_%dp%d%s.tdx", strBarType, IP_1st, IP_2nd, strIA);
    write_tydex(fullfile(stiffnessFolder, fname), tdxData);

    fprintf("(%d/%d): '%s' -> '%s'\n", k, numel(dirPat), dirPat(k).name, fname);
end

%========================
% lat only
%========================
strFilt = '*_Lat_*.tdx';
tdxTemp = "..\data\FTire_tydex_template\clat_7fz6_2p7.tdx";
tdxData = read_tydex(tdxTemp);

dirPat = dir(fullfile(stiffnessFolder, strFilt));
for k = 1:numel(dirPat)
    % read old vulcan data of possibly mismatched format
    tdxDataVulcan = read_tydex(fullfile(dirPat(k).folder, dirPat(k).name));

    % update common sections
    tdxData.header.measid.value = TR_number;
    tdxData.header.supplier.value = 'Bridgestone';
    tdxData.header.date.value = char(datetime('now', 'Format', 'd-MMM-yyyy'));
    tdxData.header.clcktime.value = char(datetime('now', 'Format', 'HH:mm:ss'));
    tdxData.comments = ['Converted on ' char(datetime("now")) '.'];

    % update constants
    tdxData.constants = update_tydex_constants(tdxData, tdxDataVulcan);

    % update measdata: assume consistent units
    tdxData.measdata.runtime = tdxDataVulcan.measdata.runtime;
    tdxData.measdata.fzw = tdxDataVulcan.measdata.fzw;
    tdxData.measdata.fyw = tdxDataVulcan.measdata.fyw;
    tdxData.measdata.latdispw = tdxDataVulcan.measdata.latdispw;

    % extract conditions
    IP = tdxData.constants.inflpres.value;
    IP_1st = floor(IP);
    IP_2nd = round((IP - IP_1st) * 10);

    FZ = str2double(tdxData.constants.fzw.value);
    FZ_1st = floor(FZ / 1000);
    FZ_2nd = floor((FZ - FZ_1st*1000) / 100);

    fname = sprintf("clat_%dfz%d_%dp%d.tdx", FZ_1st, FZ_2nd, IP_1st, IP_2nd);
    write_tydex(fullfile(stiffnessFolder, fname), tdxData);

    fprintf("(%d/%d): '%s' -> '%s'\n", k, numel(dirPat), dirPat(k).name, fname);
end

%========================
% long only
%========================
strFilt = '*_Long_*.tdx';
tdxTemp = "..\data\FTire_tydex_template\clong_7fz6_2p7.tdx";
tdxData = read_tydex(tdxTemp);

dirPat = dir(fullfile(stiffnessFolder, strFilt));
for k = 1:numel(dirPat)
    % read old vulcan data of possibly mismatched format
    tdxDataVulcan = read_tydex(fullfile(dirPat(k).folder, dirPat(k).name));

    % update common sections
    tdxData.header.measid.value = TR_number;
    tdxData.header.supplier.value = 'Bridgestone';
    tdxData.header.date.value = char(datetime('now', 'Format', 'd-MMM-yyyy'));
    tdxData.header.clcktime.value = char(datetime('now', 'Format', 'HH:mm:ss'));
    tdxData.comments = ['Converted on ' char(datetime("now")) '.'];

    % update constants
    tdxData.constants = update_tydex_constants(tdxData, tdxDataVulcan);

    % update measdata: assume consistent units
    tdxData.measdata.runtime = tdxDataVulcan.measdata.runtime;
    tdxData.measdata.fx = tdxDataVulcan.measdata.fxw;
    tdxData.measdata.fzw = tdxDataVulcan.measdata.fzw;
    tdxData.measdata.longdisp = tdxDataVulcan.measdata.longdisp;

    % extract conditions
    IP = tdxData.constants.inflpres.value;
    IP_1st = floor(IP);
    IP_2nd = round((IP - IP_1st) * 10);

    FZ = str2double(tdxData.constants.fzw.value);
    FZ_1st = floor(FZ / 1000);
    FZ_2nd = floor((FZ - FZ_1st*1000) / 100);

    fname = sprintf("clon_%dfz%d_%dp%d.tdx", FZ_1st, FZ_2nd, IP_1st, IP_2nd);
    write_tydex(fullfile(stiffnessFolder, fname), tdxData);

    fprintf("(%d/%d): '%s' -> '%s'\n", k, numel(dirPat), dirPat(k).name, fname);
end

%========================
% tors only
%========================
strFilt = '*_Tors_*.tdx';
tdxTemp = "..\data\FTire_tydex_template\ctors_2p7_7fz6.tdx";
tdxData = read_tydex(tdxTemp);

dirPat = dir(fullfile(stiffnessFolder, strFilt));
for k = 1:numel(dirPat)
    % read old vulcan data of possibly mismatched format
    tdxDataVulcan = read_tydex(fullfile(dirPat(k).folder, dirPat(k).name));

    % update common sections
    tdxData.header.measid.value = TR_number;
    tdxData.header.supplier.value = 'Bridgestone';
    tdxData.header.date.value = char(datetime('now', 'Format', 'd-MMM-yyyy'));
    tdxData.header.clcktime.value = char(datetime('now', 'Format', 'HH:mm:ss'));
    tdxData.comments = ['Converted on ' char(datetime("now")) '.'];

    % update constants
    tdxData.constants = update_tydex_constants(tdxData, tdxDataVulcan);

    % update measdata: assume consistent units
    tdxData.measdata.runtime = tdxDataVulcan.measdata.runtime;
    tdxData.measdata.fzw = tdxDataVulcan.measdata.fzw;
    tdxData.measdata.fyw = tdxDataVulcan.measdata.fyw;
    tdxData.measdata.mzw = tdxDataVulcan.measdata.mzw;
    tdxData.measdata.dstgrwhc = tdxDataVulcan.measdata.dstgrwhc;
    tdxData.measdata.steeangl = tdxDataVulcan.measdata.steeangl;

    % extract conditions
    IP = tdxData.constants.inflpres.value;
    IP_1st = floor(IP);
    IP_2nd = round((IP - IP_1st) * 10);

    FZ = str2double(tdxData.constants.fzw.value);
    FZ_1st = floor(FZ / 1000);
    FZ_2nd = floor((FZ - FZ_1st*1000) / 100);

    fname = sprintf("ctors_%dfz%d_%dp%d.tdx", FZ_1st, FZ_2nd, IP_1st, IP_2nd);
    write_tydex(fullfile(stiffnessFolder, fname), tdxData);

    fprintf("(%d/%d): '%s' -> '%s'\n", k, numel(dirPat), dirPat(k).name, fname);
end
