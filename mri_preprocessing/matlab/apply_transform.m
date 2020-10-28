function [output_img] = apply_transform(input_path, def_field, voxel_size, pref)
    if ~isfile(input_path)
       output_img = NaN;
       disp([input_path " does not exist"]);
       return
    end
    input_path = convertStringsToChars(input_path);
    [input_dir, basename, ext] = fileparts(input_path);
    if nargin < 2 || strcmp(def_field, '') || isnan(def_field)
        def_field = fullfile(input_dir, ['y_' basename ext]);
    end
    if nargin < 3
        vox = [2 2 2];
    else
        vox = [voxel_size, voxel_size, voxel_size];
    end
    if nargin < 4
        pref = 'non_linear_';
    end
    pref = convertStringsToChars(pref);
    matlabbatch{1}.spm.spatial.normalise.write.subj.def = {
        def_field
    };
    matlabbatch{1}.spm.spatial.normalise.write.subj.resample = {
        [input_path ',1']
    };
    matlabbatch{1}.spm.spatial.normalise.write.woptions.bb = [-88.5000 -125.5000 -71.5000
        89.5000  88.5000 106.5000];
%     matlabbatch{1}.spm.spatial.normalise.write.woptions.bb = [-90 -126 -72
%         90 90 108];
    matlabbatch{1}.spm.spatial.normalise.write.woptions.vox = vox;
    matlabbatch{1}.spm.spatial.normalise.write.woptions.interp = 4;
    if ~strcmp(pref, '')
        matlabbatch{1}.spm.spatial.normalise.write.woptions.prefix = pref;
        output_img = fullfile(input_dir, [pref basename ext]);
    else
        output_img = input_path;
    end

    spm_jobman('run',matlabbatch);
    clear matlabbatch;
end 