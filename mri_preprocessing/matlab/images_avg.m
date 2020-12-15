function [output_img] = images_avg(img_list, method, output_dir, out_pref)
    %IMAGES_STD Calculate the standard deviation of images in the same
    % space
    img_list = transpose(img_list);
    spm('defaults', 'FMRI');
    spm_jobman('initcfg');
    matlabbatch{1}.spm.util.imcalc.input = img_list;
    matlabbatch{1}.spm.util.imcalc.output = out_pref;
    matlabbatch{1}.spm.util.imcalc.outdir = {output_dir};
    if strcmp(method, 'mean')
        matlabbatch{1}.spm.util.imcalc.expression = 'mean(X)';
    elseif strcmp(method, 'std')
        matlabbatch{1}.spm.util.imcalc.expression = 'std(X)';
    else
        disp('ERROR: Average Method unknown (mean/std)')    
    end
        
    matlabbatch{1}.spm.util.imcalc.var = struct('name', {}, 'value', {});
    matlabbatch{1}.spm.util.imcalc.options.dmtx = 1;
    matlabbatch{1}.spm.util.imcalc.options.mask = 0;
    matlabbatch{1}.spm.util.imcalc.options.interp = 1;
    matlabbatch{1}.spm.util.imcalc.options.dtype = 4;
    spm_jobman('run', matlabbatch);
    clear matlabbatch
    output_img = fullfile(output_dir, [out_pref '.nii']);
end

