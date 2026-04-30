
% update one tydex content with another one

function constants = update_tydex_constants(existTydex, tydexContent)

constants = existTydex.constants;
fldnames = fields(constants);

for k = 1:numel(fldnames)
    fldname = fldnames{k};
    
    if isfield(tydexContent.constants, fldname)
        varConst = tydexContent.constants.(fldname);
        if strcmpi(varConst.units, 'mm') % from mm to m
            constants.(fldname).value = str2double(varConst.value) / 1000.0;
        elseif strcmpi(varConst.units, 'in') || strcmpi(varConst.units, 'inch') % from inch to m
            constants.(fldname).value = str2double(varConst.value) * 0.0254;
        elseif strcmpi(varConst.units, 'kpa') % from kPa to bar
            constants.(fldname).value = str2double(varConst.value) / 100.0;
        elseif strcmpi(varConst.units, 'm/s') % from m/s to kph
            constants.(fldname).value = str2double(varConst.value) *3.6;
        elseif strcmpi(varConst.units, 'rad') % from rad to deg
            constants.(fldname).value = rad2deg(str2double(varConst.value));
        elseif strcmpi(varConst.units, '%') && strcmpi(fldname, 'ASPRATIO') % from % to -
            constants.(fldname).value = str2double(varConst.value) / 100.0;
        else
            constants.(fldname).value = varConst.value;
        end
    end
end

end
