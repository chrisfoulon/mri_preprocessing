function [out] = run_denoise(img_path, out_dir, pref)
    opt            = struct;    
    opt.dir_out    = out_dir; % Output directory
    opt.do.denoise = true;     % Enable denoising
    if nargin > 2
        opt.prefix            = pref;
    end
    out = RunPreproc(img_path, opt);
end

