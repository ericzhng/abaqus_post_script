function [idx_range, mean_value_idx] = cut_signal_range(runtime, fzc, trajvelw, VX_mps)

    R_drum = 1.0; % m
    reserved_before_impact = 0.15;
    gap_impact_and_detected = 0.02;

    % detect the stabilization of speed
    dvdx = gradient(trajvelw);
    flat_points = find(abs(dvdx) < 1e-4);

    % The end flattening point is the first index in the last continuous block of flat_points.
    end_index = flat_points(find(diff(flat_points) > 1, 1, 'last') + 1);

    % give it a bit of space
    stable_time_cutoff = runtime(end_index) + 0.02;

    % detect the impact point
    idxs = findchangepts(fzc, 'MaxNumChanges', 5);
    if isempty(idxs); [~, idx] = max(abs(fzc)); else; idx = idxs(1); end
    impact_time_1st = runtime(idx);

    % always make sure impact_time_1st > stable_time_cutoff
    if impact_time_1st > stable_time_cutoff
        dt_gap = impact_time_1st - stable_time_cutoff;
        cutoff_time_1st = impact_time_1st - max(min(dt_gap, reserved_before_impact), 0.05);
    else
        error('  impact started before the velocity stabilizes; possibly wrongly identified impact time');
    end

    T_cycle = 2 * pi * R_drum / VX_mps;

    time_2nd_cutoff = impact_time_1st + T_cycle - gap_impact_and_detected;

    idx_range = runtime < time_2nd_cutoff & runtime > cutoff_time_1st;

    mean_value_idx = runtime < impact_time_1st - gap_impact_and_detected & runtime > stable_time_cutoff;
end
