function [out] = run_denoise(img_path, out_dir)
    opt            = struct;    
    opt.dir_out    = out_dir; % Output directory
    opt.do.denoise = true;     % Enable denoising
    out = RunPreproc(img_path, opt);
end

