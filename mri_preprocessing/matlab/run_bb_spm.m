function [out] = run_bb_spm(img_path, out_dir, voxel_size, pref)
    opt            = struct;    
    opt.dir_out    = out_dir; % Output directory
    opt.do.reslice        = true;
    opt.do.go2native   = false;
    opt.do.bb_spm = true;
    opt.do.real_mni= false;
    if nargin > 2
        opt.do.vx             = true;
        opt.vx.size = cast(voxel_size, 'double');
    end
    if nargin > 3
        opt.prefix            = pref;
    end
    out = RunPreproc(img_path, opt);
end

