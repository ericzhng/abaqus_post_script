
addpath(genpath('C:\Users\ZhangHui\Documents\1-code\ericlib\src'));
clear; clc;

% specify folder and test conditions
IP = 270;   % kPa
VX = 40;    % kph
FZ_NOM = 7563;

tirFilePath = "D:\0-data-library\Virtual\GM-FTIRE\ZG719Q\cornering\MF62_model.tir";
tydexTemp = "C:\Users\ZhangHui\Documents\1-code\1-VOE-Abaqus-Post\data\cornering_template.tdx";

%========================
% no changes afterwards
%========================

% break down pressure values
IP_hundreds = floor(IP/100);
IP_tens = floor((IP-IP_hundreds*100)/10);

% read tydex template
tydexContent = read_tydex(tydexTemp);

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
tirParams.Q_RA1 = 0.60147;
tirParams.Q_RA2 = 0.81974;
tirParams.Q_RB1 = 1.2648;
tirParams.Q_RB2 = -1.4057;

useMode = 211;  % limits check (1-on), alpha star, turn slip

% specify conditions
loads = [0.5, 1, 1.5] * FZ_NOM;
cambers = deg2rad([-5, 0, 5]);   % deg
SA_list = deg2rad(-12:1:12);

figure; hold on;

for k = 1:numel(loads)
    for m = 1:numel(cambers)
        load = loads(k);
        camber = cambers(m);

        rawInputs.ip = IP*1E3;           % [Pa]
        rawInputs.fz = load;            % [N]
        rawInputs.vx = VX / 3.6;        % [m/s]
        rawInputs.ia = camber;      % [rad]
        rawInputs.sa = SA_list;      % [rad]
        rawInputs.sr = 0 / 100;    % [-]
        rawInputs.phit = 0.0;           % [1/m]

        % MFEval eqns
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
        plot(rad2deg(slipangl), FY, '-');

        % extract conditions
        FZ_scale = FZ(1);
        IA_scale = rad2deg(inclangl(1));
        Vx_scale = abs(VX(1)) * 3.6;    % kph

        % allocate dummy arrays
        nsize = numel(FZ);
        bzeros = zeros(nsize, 1);

        tydexContent.measdata.tyredefw = bzeros;
        tydexContent.measdata.vertvelw = bzeros;

        tydexContent.measdata.slipangl = slipangl;
        tydexContent.measdata.inclangl = inclangl;
        tydexContent.measdata.longslip = longslip;
        tydexContent.measdata.dstgrwhc = Rl;
        tydexContent.measdata.fx = FX;
        tydexContent.measdata.fyw = FY;
        tydexContent.measdata.fzw = FZ;
        tydexContent.measdata.mxw = MX;
        tydexContent.measdata.myw = MY;
        tydexContent.measdata.mzw = MZ;

        % conditions
        tydexContent.constants.fzw.value = FZ_scale;
        tydexContent.constants.inclangl.value = IA_scale;
        tydexContent.constants.longvel.value = Vx_scale;

        % for cornering, no need slipangl in constant
        if isfield(tydexContent.constants, "slipangl")
            tydexContent.constants = rmfield(tydexContent.constants, "slipangl");
        end

        % break down FZ in components
        FZ_thousands = floor(FZ_scale/1000);
        FZ_hundreds = floor((FZ_scale-FZ_thousands*1000)/100);

        fname = sprintf("side_%dp%d_%dfz%d_%.0fv_%.0fcam.tdx", IP_hundreds, IP_tens, FZ_thousands, FZ_hundreds, Vx_scale, IA_scale);
        write_tydex(fullfile(fileparts(tirFilePath), fname), tydexContent);
    end
end
