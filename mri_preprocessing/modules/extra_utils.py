import shutil
from pathlib import Path
import os
import time
import json
import importlib_resources as rsc

import matlab.engine
from mri_preprocessing.modules import preproc, utils
from bcblib.tools.nifti_utils import is_nifti

pref_dict = {
    'geomean_denoise_': 'denoise',
    'resliced_co-rigid_rigid_geomean_denoise_': 'rigid',
    'resliced_co-affine_affine_geomean_denoise_': 'affine',
    'non_linear_co-rigid_rigid_geomean_denoise_': 'nonlinear',
}


def fill_up_dict_from_folder(output_folder):
    output_dict = {
        'denoise': {},
        'rigid': {},
        'affine': {},
        'nonlinear': {},
        'def_field': {},
        'inv_def_field': {},
    }
    bval_set = set()
    for f in Path(output_folder).iterdir():
        if is_nifti(f):
            bval = f.name.split('__bval')[-1].split('.nii')[0] + '.0'
            bval_set.add(bval)
            for pref in pref_dict:
                if f.name.startswith(pref):
                    output_dict[pref_dict[pref]][bval] = str(f)
    for f in Path(output_folder, 'tmp').rglob('*'):
        if f.name.startswith('y_co-rigid_rigid_geomean_denoise_'):
            output_dict['def_field'] = {b: str(f) for b in bval_set}
        elif f.name.startswith('iy_co-rigid_rigid_geomean_denoise_'):
            output_dict['inv_def_field'] = {b: str(f) for b in bval_set}
    return output_dict


def apply_transform_dataset(root_folder, output_vox_size=2):
    matlab_scripts_folder = rsc.files('mri_preprocessing.matlab')

    engine = matlab.engine.start_matlab()
    engine.addpath(str(matlab_scripts_folder))
    # Just in case we add all of them
    engine.addpath(preproc.spm_path)
    engine.addpath(preproc.superres_path)
    engine.addpath(preproc.patient_preproc_path)

    missing_reg_folders = [d for d in Path(root_folder).rglob('*')
                           if d.is_dir() and '__preproc_dict.json' not in [f.name for f in d.iterdir()] and
                           d.name != 'tmp']
    partial_final_preproc_dict = {}
    for d in missing_reg_folders:
        key = Path(d).name
        preproc_dict = fill_up_dict_from_folder(d)
        # print(preproc_dict)
        # return
        if preproc_dict['rigid'] != {} and preproc_dict['def_field'] != {}:
            for bval in preproc_dict['rigid']:
                original_rigid = preproc_dict['rigid'][bval].replace('resliced_', 'tmp/')
                output_img = engine.apply_transform(original_rigid, preproc_dict['def_field'][bval],
                                                    output_vox_size)
                output_img_new_path = Path(d, Path(output_img).name)
                shutil.copyfile(output_img, output_img_new_path)
                preproc_dict['nonlinear'][bval] = str(output_img_new_path)
            partial_final_preproc_dict[key] = preproc_dict
        with open(Path(d, '__preproc_dict.json'), 'w+') as j:
            json.dump({key: preproc_dict}, j, indent=4)
    # if Path(root_folder, '__final_preproc_dict.json').is_file():
    #     final_preproc_dict = json.load(open(Path(root_folder, '__final_preproc_dict.json'), 'r'))
    #     partial_final_preproc_dict.update(final_preproc_dict)
    # with open(Path(root_folder, '__final_preproc_dict.json'), 'w+') as j:
    #     json.dump(partial_final_preproc_dict, j, indent=4)
    utils.generate_final_preproc_dict(root_folder)
    return partial_final_preproc_dict

