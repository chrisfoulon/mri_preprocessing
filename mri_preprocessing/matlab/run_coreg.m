function [out] = run_coreg(images, out_dir)
    opt            = struct;    
    opt.dir_out    = out_dir; % Output directory
    opt.do.coreg        = true;
   
    out = RunPreproc(imgs, opt);
end
