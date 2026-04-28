
addpath(genpath('C:\Users\ZhangHui\Documents\1-code\ericlib\src'));
clear; clc;

spec = 'ZI727Q';

% specify root directory for ftire raw data
if strcmpi(spec, 'ZG719Q')
    rootDir = "D:\0-data-library\FTire\GM-FTire\FTire_ZG719Q_275_50R22_T23-01204\Virtual_PV\raw";
    TR_number = 'T23-01204';

    % use a Vulcan tydex with correct tire size and nominal pressure
    tdxFile = fullfile(rootDir, "stiffness", 'A-27348_TotalStiff_Flat_Tors_11344N_270kPa.tdx');
elseif strcmpi(spec, 'ZI727Q')
    rootDir = "D:\0-data-library\FTire\GM-FTire\FTire_ZI727Q_255_55R20_T20-00968\Virtual_PV\raw";
    TR_number = 'T20-00968';

    tdxFile = fullfile(rootDir, "stiffness", 'A-24690_TotalStiff_Flat_Lat_6450N_270kPa.tdx');
end

brakingFolder = fullfile(rootDir, "braking");
corneringFolder = fullfile(rootDir, "cornering");

%========================
% no changes afterwards
%========================

% only for getting basic tire info
tdxInfo = read_tydex(tdxFile);

%========================
% muslip
%========================

% for tydex template consistent with ftire
tdxTemp = "..\data\FTire_tydex_template\side_2p7_7fz6_50v.tdx";
tdxData = read_tydex(tdxTemp);

figure; hold on;
strFilt = 'Braking_*.csv';
dirPat = dir(fullfile(brakingFolder, strFilt));
for k = 1:numel(dirPat)
    % read csv
    Tab = readtable(fullfile(dirPat(k).folder, dirPat(k).name));

    [runtime, Slip_new] = triangle_curve(Tab.Slip, 0.2, 5/100.0); % unit in 1/100

    % needs to expand the data to have more data points
    FX_new = spline(Tab.Slip, Tab.FX, Slip_new);
    FY_new = spline(Tab.Slip, Tab.FY, Slip_new);
    FZ_new = spline(Tab.Slip, Tab.FZ, Slip_new);
    MZ_new = spline(Tab.Slip, Tab.MZ, Slip_new);
    LR_new = spline(Tab.Slip, Tab.LR, Slip_new);

    plot(Slip_new, FX_new);

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
    nsize = numel(Slip_new);

    % update measdata: assume consistent units
    tdxData.measdata.runtime = runtime;
    tdxData.measdata.fx = FX_new;
    tdxData.measdata.fzw = FZ_new;
    tdxData.measdata.fyw = FY_new;
    tdxData.measdata.mzw = MZ_new;
    tdxData.measdata.dstgrwhc = LR_new;
    tdxData.measdata.slipangl = zeros(nsize, 1);
    tdxData.measdata.longslip = Slip_new * 100; % in percentage

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
    write_tydex(fullfile(rootDir, fname), tdxData);

    fprintf("(%d/%d): '%s' -> '%s'\n", k, numel(dirPat), dirPat(k).name, fname);
end

%========================
% side
%========================

% for tydex template consistent with ftire
tdxTemp = "..\data\FTire_tydex_template\side_2p7_7fz6_50v.tdx";
tdxData = read_tydex(tdxTemp);

figure; hold on;

strFilt = 'cornering_*.csv';
dirPat = dir(fullfile(corneringFolder, strFilt));
for k = 1:numel(dirPat)
    % read csv
    Tab = readtable(fullfile(dirPat(k).folder, dirPat(k).name));

    if abs(Tab.IA(1)) < 1E-3
        % make sure Tab.Slip contains 0 degree
        if Tab.Slip(end) ~= 0
            error('Ensure you have added freerolling data to cornering csv files');
        end

        % get SA_plysteer
        pp = polyfit(Tab.FY(end-3:end), Tab.Slip(end-3:end), 1);
        SA_plysteer = pp(end);

        % zero camber case, flip data to full curve
        Slip_full = [Tab.Slip(1:end-1); -flip(Tab.Slip) + 2 * SA_plysteer];
        FX_full = [Tab.FX(1:end-1); -flip(Tab.FX)];
        FY_full = [Tab.FY(1:end-1); -flip(Tab.FY)];
        FZ_full = [Tab.FZ(1:end-1); flip(Tab.FZ)];
        MX_full = [Tab.MX(1:end-1); -flip(Tab.MX)];
        MZ_full = [Tab.MZ(1:end-1); -flip(Tab.MZ)];
        LR_full = [Tab.LR(1:end-1); flip(Tab.LR)];
    else
        Slip_full = Tab.Slip;
        FX_full = Tab.FX;
        FY_full = Tab.FY;
        FZ_full = Tab.FZ;
        MX_full = Tab.MX;
        MZ_full = Tab.MZ;
        LR_full = Tab.LR;
    end

    [runtime, Slip_new] = triangle_curve(Slip_full, 0.25, 2);

    FX_new = spline(Slip_full, FX_full, Slip_new);
    FY_new = spline(Slip_full, FY_full, Slip_new);
    FZ_new = spline(Slip_full, FZ_full, Slip_new);
    MX_new = spline(Slip_full, MX_full, Slip_new);
    MZ_new = spline(Slip_full, MZ_full, Slip_new);
    LR_new = spline(Slip_full, LR_full, Slip_new);

    plot(Slip_new, FY_new);

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
    tdxData.constants.longvel.value = 100; % use 100 kph instead of VX kph

    % allocate dummy arrays
    nsize = numel(Slip_new);

    % update measdata: assume consistent units
    tdxData.measdata.runtime = runtime;
    tdxData.measdata.fx = FX_new;
    tdxData.measdata.fzw = FZ_new;
    tdxData.measdata.fyw = FY_new;
    tdxData.measdata.mzw = MZ_new / 1000.0;
    tdxData.measdata.dstgrwhc = LR_new;
    tdxData.measdata.slipangl = Slip_new; % in deg
    tdxData.measdata.longslip = zeros(nsize, 1);

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
    write_tydex(fullfile(rootDir, fname), tdxData);

    fprintf("(%d/%d): '%s' -> '%s'\n", k, numel(dirPat), dirPat(k).name, fname);
end
