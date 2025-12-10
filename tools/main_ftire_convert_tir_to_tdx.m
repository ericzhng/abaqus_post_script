
addpath(genpath('C:\Users\ZhangHui\Documents\1-code\ericlib\src'));
clear; clc;

% specify root directory for ftire raw data
rootDir = "D:\0-data-library\Virtual\GM-FTIRE\ZG719Q";

brakingFolder = fullfile(rootDir, "braking");
corneringFolder = fullfile(rootDir, "cornering");

tirFilePath = fullfile(corneringFolder, "MF62_model.tir");

% use a Vulcan tydex with correct nominal pressure
tdxInfo = fullfile(rootDir, "stiffness", 'A-27348_TotalStiff_Flat_Lat_7563N_270kPa.tdx');

TR_number = 'T23-01204';

% specify folder and test conditions
IP = 270;   % kPa
Vc = 40;    % kph
FZ_NOM = 7563;

%========================
% no changes afterwards
%========================

% only for getting basic tire info
tdxInfo = read_tydex(tdxInfo);

% for tydex template consistent with ftire
tdxTemp = "..\data\FTire_tydex_template\side_2p7_7fz6_50v.tdx";
tdxData = read_tydex(tdxTemp);

% specify conditions
loads = [0.5, 1, 1.5] * FZ_NOM;
cambers = deg2rad([-5, 0, 5]);   % deg
SR_list = (-20:1:20) / 100.0;
SA_list = deg2rad(-12:1:12);

% break down pressure values
IP_1st = floor(IP/100);
IP_2nd = floor((IP - IP_1st*100)/10);

% read tir
outdata = read_tir(tirFilePath);
tirParams = table2struct( ...
    [ ...
    struct2table( outdata.MODEL ), ...
    struct2table( outdata.DIMENSION ), ...
    struct2table( outdata.OPERATING_CONDITIONS ), ...
    struct2table( outdata.VERTICAL ), ...
    struct2table( outdata.STRUCTURAL ), ...
    struct2table( outdata.VERTICAL_FORCE_RANGE ), ...
    struct2table( outdata.INFLATION_PRESSURE_RANGE ), ...
    struct2table( outdata.LONG_SLIP_RANGE ), ...
    struct2table( outdata.SLIP_ANGLE_RANGE ), ...
    struct2table( outdata.INCLINATION_ANGLE_RANGE ), ...
    struct2table( outdata.SCALING_COEFFICIENTS ), ...
    struct2table( outdata.LONGITUDINAL_COEFFICIENTS ), ...
    struct2table( outdata.LATERAL_COEFFICIENTS ), ...
    struct2table( outdata.OVERTURNING_COEFFICIENTS ), ...
    struct2table( outdata.ROLLING_COEFFICIENTS ), ...
    struct2table( outdata.ALIGNING_COEFFICIENTS ), ...
    ]);
% ensure missing ones are included
tirParams.Q_RA1 = 0.60147;
tirParams.Q_RA2 = 0.81974;
tirParams.Q_RB1 = 1.2648;
tirParams.Q_RB2 = -1.4057;

useMode = 211;  % limits check (1-on), alpha star, turn slip

%========================
% muslip
%========================

figure; hold on;
for k = 1:numel(loads)
    for m = 1:numel(cambers)
        id = m + (k-1)*numel(cambers);
        load = loads(k);
        camber = cambers(m);

        rawInputs.ip = IP*1E3;      % [Pa]
        rawInputs.vx = Vc / 3.6;    % [m/s]
        rawInputs.fz = load;        % [N]
        rawInputs.ia = camber;      % [rad]
        rawInputs.sa = 0.0;         % [rad]
        rawInputs.sr = SR_list;     % -
        rawInputs.phit = 0.0;       % [1/m]

        unifyInputs = mf_sub_unify_inputs(tirParams, rawInputs);
        inputs = [unifyInputs.fz unifyInputs.sr unifyInputs.sa unifyInputs.ia unifyInputs.phit unifyInputs.vx unifyInputs.ip];
        output = mfeval(tirParams, inputs, useMode);

        FX = output(:,1);
        FY = output(:,2);
        FZ = output(:,3);
        MX = output(:,4);
        MY = output(:,5);
        MZ = output(:,6);
        longslip = output(:,7);
        slipangl = output(:,8);
        inclangl = output(:,9);
        VX = output(:,11);
        Rl = output(:,20);
        Re = output(:,13);

        % plot
        plot(longslip * 100, FX, '-');
        % plot(rad2deg(slipangl), FY, '-');
    
        % update common sections
        tdxData.header.measid.value = TR_number;
        tdxData.header.supplier.value = 'Bridgestone';
        tdxData.header.date.value = char(datetime('now', 'Format', 'd-MMM-yyyy'));
        tdxData.header.clcktime.value = char(datetime('now', 'Format', 'HH:mm:ss'));
        tdxData.comments = ['Converted on ' char(datetime("now")) '.'];
    
        % update constants
        tdxData.constants = update_tydex_constants(tdxData, tdxInfo);
    
        % update specific constants
        tdxData.constants.fzw.value = load;
        tdxData.constants.inclangl.value = rad2deg(camber);
        tdxData.constants.longvel.value = Vc;

        % allocate dummy arrays
        nsize = numel(FZ);
    
        % update measdata: assume consistent units
        tdxData.measdata.runtime = (1:nsize)' * 0.1;
        tdxData.measdata.fx = FX;
        tdxData.measdata.fyw = FY;
        tdxData.measdata.fzw = FZ;
        tdxData.measdata.mzw = MZ;
        tdxData.measdata.dstgrwhc = Rl;
        tdxData.measdata.slipangl = slipangl;
        tdxData.measdata.longslip = longslip;
    
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

        fname = sprintf("muslip_%dp%d_%dfz%d_%.fv%s.tdx", IP_1st, IP_2nd, FZ_1st, FZ_2nd, Vc, strIA);
        write_tydex(fullfile(fileparts(tirFilePath), fname), tdxData);

        fprintf("(%d/%d): '%s'\n", id, numel(loads)*numel(cambers), fname);
    end
end

%========================
% side
%========================

figure; hold on;
for k = 1:numel(loads)
    for m = 1:numel(cambers)
        id = m + (k-1)*numel(cambers);
        load = loads(k);
        camber = cambers(m);

        rawInputs.ip = IP*1E3;      % [Pa]
        rawInputs.vx = Vc / 3.6;    % [m/s]
        rawInputs.fz = load;        % [N]
        rawInputs.ia = camber;      % [rad]
        rawInputs.sa = SA_list;     % [rad]
        rawInputs.sr = 0.0;         % -
        rawInputs.phit = 0.0;       % [1/m]

        unifyInputs = mf_sub_unify_inputs(tirParams, rawInputs);
        inputs = [unifyInputs.fz unifyInputs.sr unifyInputs.sa unifyInputs.ia unifyInputs.phit unifyInputs.vx unifyInputs.ip];
        output = mfeval(tirParams, inputs, useMode);

        FX = output(:,1);
        FY = output(:,2);
        FZ = output(:,3);
        MX = output(:,4);
        MY = output(:,5);
        MZ = output(:,6);
        longslip = output(:,7);
        slipangl = output(:,8);
        inclangl = output(:,9);
        VX = output(:,11);
        Rl = output(:,20);
        Re = output(:,13);

        % plot
        % plot(longslip * 100, FX, '-');
        plot(rad2deg(slipangl), FY, '-');
    
        % update common sections
        tdxData.header.measid.value = TR_number;
        tdxData.header.supplier.value = 'Bridgestone';
        tdxData.header.date.value = char(datetime('now', 'Format', 'd-MMM-yyyy'));
        tdxData.header.clcktime.value = char(datetime('now', 'Format', 'HH:mm:ss'));
        tdxData.comments = ['Converted on ' char(datetime("now")) '.'];
    
        % update constants
        tdxData.constants = update_tydex_constants(tdxData, tdxInfo);
    
        % update specific constants
        tdxData.constants.fzw.value = load;
        tdxData.constants.inclangl.value = rad2deg(camber);
        tdxData.constants.longvel.value = Vc;

        % allocate dummy arrays
        nsize = numel(FZ);
    
        % update measdata: assume consistent units
        tdxData.measdata.runtime = (1:nsize)' * 0.1;
        tdxData.measdata.fx = FX;
        tdxData.measdata.fyw = FY;
        tdxData.measdata.fzw = FZ;
        tdxData.measdata.mzw = MZ;
        tdxData.measdata.dstgrwhc = Rl;
        tdxData.measdata.slipangl = slipangl;
        tdxData.measdata.longslip = longslip;
    
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

        fname = sprintf("side_%dp%d_%dfz%d_%.fv%s.tdx", IP_1st, IP_2nd, FZ_1st, FZ_2nd, Vc, strIA);
        write_tydex(fullfile(fileparts(tirFilePath), fname), tdxData);

        fprintf("(%d/%d): '%s'\n", id, numel(loads)*numel(cambers), fname);
    end
end
