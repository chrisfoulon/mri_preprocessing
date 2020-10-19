function [out] = preproc(img_path, out_dir)
disp(img_path);

opt            = struct;    
opt.dir_out    = out_dir; % Output directory
opt.do.denoise = true;     % Enabla denoising
%opt.do.coreg    = true;     % Co-register using NMI
%opt.do.reslice  = true;     % Reslice to have same image grids


% opt.do.real_mni = true;    %affine align to mni
% opt.realign2mni.rigid = true;
% opt.do.go2native      = false;
% opt.do.bb_spm         = true;
% opt.do.vx             = true;
% opt.vx.size = 2;
out = RunPreproc(img_path, opt);