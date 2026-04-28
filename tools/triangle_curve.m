
function [runtime, var_start_zero] = triangle_curve(data, step_size, rate)

abs_amp = max(abs(data));

curve_1st = (0 : step_size * rate : abs_amp);
curve_2nd = (abs_amp : -step_size * rate : -abs_amp);
curve_3rd = (-abs_amp : step_size * rate : 0);

var_start_zero = [curve_1st, curve_2nd(2:end), curve_3rd(2:end)]';
runtime = (0:numel(var_start_zero)-1)' * step_size;

end
