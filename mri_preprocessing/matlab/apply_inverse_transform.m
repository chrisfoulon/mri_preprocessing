function [output_img] = apply_inverse_transform(input_path, def_field, pref)
    if ~isfile(input_path)
       output_img = NaN;
       disp([input_path " does not exist"]);
       return
    end
    input_path = convertStringsToChars(input_path);
    [input_dir, basename, ext] = fileparts(input_path);
    pref = convertStringsToChars(pref);
    matlabbatch{1}.spm.spatial.normalise.write.subj.def = {def_field};
    matlabbatch{1}.spm.spatial.normalise.write.subj.resample = {[input_path ',1']};
    matlabbatch{1}.spm.spatial.normalise.write.woptions.bb = [nan nan nan; nan nan nan];
    matlabbatch{1}.spm.spatial.normalise.write.woptions.vox = [nan nan nan];
    matlabbatch{1}.spm.spatial.normalise.write.woptions.interp = 0;
    if ~strcmp(pref, '')
        matlabbatch{1}.spm.spatial.normalise.write.woptions.prefix = pref;
        output_img = fullfile(input_dir, [pref basename ext]);
    else
        output_img = input_path;
    end
    spm_jobman('run', matlabbatch);
    clear matlabbatch
end
