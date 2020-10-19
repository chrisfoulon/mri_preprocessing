function [out] = run_bb_spm(img_path, out_dir, voxel_size)
    opt            = struct;    
    opt.dir_out    = out_dir; % Output directory
    opt.do.bb_spm         = true;
    if nargin > 2
        opt.do.vx             = true;
        opt.vx.size = cast(voxel_size, 'double');
    end
    out = RunPreproc(img_path, opt);
end

