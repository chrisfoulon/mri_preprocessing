function [output_img] = non_linear_reg(input_path, pref, voxel_size)
    
    if ~isfile(input_path)
       output_img = NaN;
       disp([input_path " does not exist"]);
       return
    end
    input_path = convertStringsToChars(input_path);
    [input_dir,basename,ext] = fileparts(convertStringsToChars(input_path));
    if nargin < 2
        pref = 'non_linear_';
    end
    pref = convertStringsToChars(pref);
    
    output_img = input_path;
    spm('defaults', 'FMRI');
    spm_jobman('initcfg');
    
    tpm_file = fullfile(spm('dir'),'tpm','TPM.nii');
    %tpm_path=[matlabroot '\toolbox\spm12\tpm\'];
    display(input_path);
%     rigid_align(input_path, 1);
    
    matlabbatch{1}.spm.spatial.preproc.channel.vols = {input_path};
    matlabbatch{1}.spm.spatial.preproc.channel.biasreg = 0.001;
    matlabbatch{1}.spm.spatial.preproc.channel.biasfwhm = 60;
    matlabbatch{1}.spm.spatial.preproc.channel.write = [0 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(1).tpm = {[tpm_file ',1']};
    matlabbatch{1}.spm.spatial.preproc.tissue(1).ngaus = 1;
    matlabbatch{1}.spm.spatial.preproc.tissue(1).native = [1 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(1).warped = [0 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(2).tpm = {[tpm_file ',2']};
    matlabbatch{1}.spm.spatial.preproc.tissue(2).ngaus = 1;
    matlabbatch{1}.spm.spatial.preproc.tissue(2).native = [1 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(2).warped = [0 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(3).tpm = {[tpm_file ',3']};
    matlabbatch{1}.spm.spatial.preproc.tissue(3).ngaus = 2;
    matlabbatch{1}.spm.spatial.preproc.tissue(3).native = [1 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(3).warped = [0 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(4).tpm = {[tpm_file ',4']};
    matlabbatch{1}.spm.spatial.preproc.tissue(4).ngaus = 3;
    matlabbatch{1}.spm.spatial.preproc.tissue(4).native = [1 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(4).warped = [0 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(5).tpm = {[tpm_file ',5']};
    matlabbatch{1}.spm.spatial.preproc.tissue(5).ngaus = 4;
    matlabbatch{1}.spm.spatial.preproc.tissue(5).native = [1 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(5).warped = [0 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(6).tpm = {[tpm_file ',6']};
    matlabbatch{1}.spm.spatial.preproc.tissue(6).ngaus = 2;
    matlabbatch{1}.spm.spatial.preproc.tissue(6).native = [0 0];
    matlabbatch{1}.spm.spatial.preproc.tissue(6).warped = [0 0];
    matlabbatch{1}.spm.spatial.preproc.warp.mrf = 1;
    matlabbatch{1}.spm.spatial.preproc.warp.cleanup = 1;
    matlabbatch{1}.spm.spatial.preproc.warp.reg = [0 0.001 0.5 0.05 0.2];
    matlabbatch{1}.spm.spatial.preproc.warp.affreg = 'mni';
    matlabbatch{1}.spm.spatial.preproc.warp.fwhm = 0;
    matlabbatch{1}.spm.spatial.preproc.warp.samp = 3;
    matlabbatch{1}.spm.spatial.preproc.warp.write = [0 1];
    output_list = spm_jobman('run',matlabbatch);
    disp(output_list);
    clear matlabbatch;
    matlabbatch{1}.spm.spatial.normalise.write.subj.def = {
        fullfile(input_dir, ['y_' basename ext])
    };
    matlabbatch{1}.spm.spatial.normalise.write.subj.resample = {
        [input_path ',1']
    };
    matlabbatch{1}.spm.spatial.normalise.write.woptions.bb = [nan nan nan, nan nan nan];
    if nargin > 2
        vox = [voxel_size, voxel_size, voxel_size];
    else
        vox = [2 2 2];
    end
    matlabbatch{1}.spm.spatial.normalise.write.woptions.vox = vox;
    matlabbatch{1}.spm.spatial.normalise.write.woptions.interp = 4;
    if ~strcmp(pref, '')
        matlabbatch{1}.spm.spatial.normalise.write.woptions.prefix = pref;
    end
    spm_jobman('run',matlabbatch);
    clear matlabbatch;
end

