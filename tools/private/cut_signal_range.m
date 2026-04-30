function [idx_range, mean_value_idx, flag_early_impact] = cut_signal_range(runtime, fzc, trajvelw)

    R_drum = 1.0; % m
    reserved_before_impact = 0.10;
    gap_impact_and_detected = 0.01;

    % detect the stabilization of speed
    dvdx = gradient(trajvelw);
    flat_points = find(abs(dvdx) < 1e-4);

    % The end flattening point is the first index in the last continuous block of flat_points.
    end_index = flat_points(find(diff(flat_points) > 1, 1, 'last') + 1);

    VX_stable = mean(trajvelw(end_index:end)) / 3.6;
    T_cycle = 2 * pi * R_drum / VX_stable;

    % give it a bit of space
    stable_time_cutoff = runtime(end_index) + 0.02;

    % detect the impact point
    index = runtime > stable_time_cutoff;
    idx_cut = find(index, 1);
    index = runtime > stable_time_cutoff + T_cycle;
    idx_cut_2 = find(index, 1);
    fzc(runtime < stable_time_cutoff) = fzc(idx_cut);
    fzc(runtime > stable_time_cutoff + T_cycle) = fzc(idx_cut_2);

    idxs = findchangepts(fzc, 'MaxNumChanges', 5);
    if isempty(idxs); [~, idx] = max(abs(fzc)); else; idx = idxs(1); end
    impact_time_1st = runtime(idx);

    % always make sure impact_time_1st > stable_time_cutoff
    dt_gap = impact_time_1st - stable_time_cutoff;
    cutoff_time_1st = impact_time_1st - max(min(dt_gap, reserved_before_impact), 0.05);

    time_2nd_cutoff = impact_time_1st + T_cycle - gap_impact_and_detected;

    idx_range = runtime < time_2nd_cutoff & runtime > cutoff_time_1st;

    if abs(impact_time_1st - stable_time_cutoff) < 0.05
        flag_early_impact = true;
        mean_value_idx = runtime < impact_time_1st & runtime > stable_time_cutoff;
    else
        flag_early_impact = false;
        mean_value_idx = runtime < impact_time_1st - gap_impact_and_detected & runtime > stable_time_cutoff;
    end

end
