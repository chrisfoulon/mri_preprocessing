function [out] = run_coreg(images, out_dir)
    if ~isa(images, 'cell')
        disp('Error: images must be a cell array containing several images');
        out = NaN;
        return
    end
    opt            = struct;    
    opt.dir_out    = out_dir; 
    opt.do.coreg        = true;
   
    out = RunPreproc(images, opt);
end
