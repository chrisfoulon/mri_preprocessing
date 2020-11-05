function [out] = run_coreg(images, out_dir, pref)
    if ~isa(images, 'cell')
        disp('Error: images must be a cell array containing several images');
        out = NaN;
        return
    end
    opt            = struct;    
    opt.dir_out    = out_dir; 
    opt.do.coreg        = true;
    
    if nargin > 2
        opt.prefix            = pref;
    end
   
    out = RunPreproc(images, opt);
end
