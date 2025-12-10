
addpath(genpath('C:\Users\ZhangHui\Documents\1-code\ericlib\src'));
clear; clc;

% specify folder and test conditions
IP = 270;   % kPa

folderBraking = "D:\0-data-library\Virtual\GM-FTIRE\ZI272Q\braking";
tydexTemp = "D:\0-data-library\Virtual\GM-FTIRE\ZI272Q\braking\cornering-template.tdx";

%========================
% no changes afterwards
%========================

% break down pressure values
IP_hundreds = floor(IP/100);
IP_tens = floor((IP-IP_hundreds*100)/10);

% read tydex template
tydexContent = read_tydex(tydexTemp);

% check all existing csv files
pat = fullfile(folderBraking, "*.csv");
dirPat = dir(pat);

for k = 1:numel(dirPat)
    fprintf("Write Tydex file (%d/%d) for %s\n", k, numel(dirPat), dirPat(k).name);

    % read csv
    csvFile = fullfile(dirPat(k).folder, dirPat(k).name);
    T = readtable(csvFile);

    % extract conditions
    FZ = T.FZ(1);
    IA = T.IA(1);
    Vx = abs(T.VX(1)) * 3.6;

    % allocate dummy arrays
    nsize = numel(T.Slip);
    bzeros = zeros(nsize, 1);
    bones = ones(nsize, 1);

    tydexContent.measdata.myw = bzeros;
    tydexContent.measdata.slipangl = bzeros;
    tydexContent.measdata.tyredefw = bzeros;
    tydexContent.measdata.vertvelw = bzeros;

    tydexContent.measdata.inclangl = T.IA;
    tydexContent.measdata.longslip = T.Slip;
    tydexContent.measdata.fx = T.FX;
    tydexContent.measdata.dstgrwhc = T.LR;
    tydexContent.measdata.fyw = T.FY;
    tydexContent.measdata.fzw = T.FZ;
    tydexContent.measdata.mxw = T.MX;
    tydexContent.measdata.mzw = T.MZ;

    % conditions
    tydexContent.constants.fzw.value = FZ;
    tydexContent.constants.inclangl.value = IA;
    tydexContent.constants.longvel.value = Vx;

    % for braking, no need longslip in constant
    if isfield(tydexContent.constants, "longslip")
        tydexContent.constants = rmfield(tydexContent.constants, "longslip");
    end

    % break down FZ in components
    FZ_thousands = floor(FZ/1000);
    FZ_hundreds = floor((FZ-FZ_thousands*1000)/100);

    fname = sprintf("muslip_%dp%d_%dfz%d_%.0fv.tdx", IP_hundreds, IP_tens, FZ_thousands, FZ_hundreds, Vx);
    write_tydex(fullfile(folderBraking, fname), tydexContent);
end
