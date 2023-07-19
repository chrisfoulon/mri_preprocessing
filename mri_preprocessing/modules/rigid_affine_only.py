import os
from pathlib import Path
import importlib_resources as rsc

import matlab

from mri_preprocessing.modules.preproc import nii_gmean, check_spm_modules

from mri_preprocessing.modules import matlab_wrappers


spm_path = ''
superres_path = ''
patient_preproc_path = ''

def rigid_affine_only(img_paths_list, output_dir, output_vox_size=2):
    check_spm_modules()
    engine = matlab.engine.start_matlab()
    matlab_scripts_folder = rsc.files('mri_preprocessing.matlab')
    engine.addpath(str(matlab_scripts_folder))
    # Just in case we add all of them
    engine.addpath(spm_path)
    engine.addpath(superres_path)
    engine.addpath(patient_preproc_path)
    engine.cd(patient_preproc_path + '/private')
    os.makedirs(output_dir, exist_ok=True)
    tmp_folder = Path(output_dir, 'tmp/')
    os.makedirs(tmp_folder, exist_ok=True)
    output_dict = {}
    for img_path in img_paths_list:
        output_dict['input_path'] = img_path
        output_reset = matlab_wrappers.reset_orient_mat(engine, img_path, Path(tmp_folder))
        output_dict['reset_origin'] = output_reset
        print('######################')
        print('RIGID AND AFFINE ALIGNMENT OF THE GEOMEAN IMAGES')
        print('######################')
        out_align = engine.my_align(output_reset, tmp_folder)
        output_dict['rigid'] = out_align['rigid']
        output_dict['affine'] = out_align['affine']
        print('######################')
        print('RESLICING')
        print('######################')
        output_dict['rigid_resliced'] = engine.run_bb_spm(
            out_align['rigid'], output_dir, output_vox_size, 'resliced_')['pth']['im'][0]
        output_dict['rigid']['affine_resliced'] = engine.run_bb_spm(
            out_align['affine'], output_dir, output_vox_size, 'resliced_')['pth']['im'][0]