import json
import os
from pathlib import Path
import importlib_resources as rsc

import matlab
import nibabel as nib
from bcblib.tools.nifti_utils import load_nifti

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
        output_dict['affine_resliced'] = engine.run_bb_spm(
            out_align['affine'], output_dir, output_vox_size, 'resliced_')['pth']['im'][0]
    return output_dict


def rigid_affine_only_img_mask(img_mask_dict, output_dir, output_vox_size=2, img_key=None, mask_key=None):
    """

    Parameters
    ----------
    img_mask_dict: dict
        The dictionary can be of 3 forms:
            1) {'img_path': 'mask_path'}
            2) {'img_path': {mask_key: 'mask_path'}
            3) {img_key: img_path, mask_key: mask_path}
    output_dir
    output_vox_size
    img_key: str or None
        if not None, implies that the dictionary is of type 3)
    mask_key: str or None
        if not None, implies that the dictionary is of type 2) or 3)

    Returns
    -------

    """
    if not isinstance(img_mask_dict, dict):
        img_mask_dict = json.load(open(img_mask_dict, 'r'))
    if img_key is not None and mask_key is None:
        raise ValueError('If img_key is not None, mask_key cannot be None')
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
    for key in img_mask_dict:
        if img_key is not None:
            img_path = img_mask_dict[img_key]
        else:
            img_path = key
        if mask_key is not None:
            mask_path = img_mask_dict[mask_key]
        else:
            mask_path = img_mask_dict[key]
        output_dict['input_path'] = img_path
        output_reset = matlab_wrappers.reset_orient_mat(engine, img_path, Path(tmp_folder))
        output_dict['reset_origin'] = output_reset
        # same but with mask_path
        output_dict['mask_path'] = mask_path
        output_reset_mask = matlab_wrappers.reset_orient_mat(engine, mask_path, Path(tmp_folder))
        output_dict['reset_origin_mask'] = output_reset_mask
        print('######################')
        print('RIGID AND AFFINE ALIGNMENT OF THE GEOMEAN IMAGES')
        print('######################')
        out_align = engine.my_align(output_reset, tmp_folder)
        output_dict['rigid'] = out_align['rigid']
        output_dict['affine'] = out_align['affine']
        # load rigid and affine images and reset_origin_mask and create 2 new mask niftiImages with the same affine
        # as the rigid and affine images
        nii_rigid = load_nifti(output_dict['rigid'])
        nii_affine = load_nifti(output_dict['affine'])
        nii_mask = load_nifti(output_dict['reset_origin_mask'])
        nii_rigid_mask = nib.Nifti1Image(nii_mask.get_data(), nii_rigid.affine)
        nii_affine_mask = nib.Nifti1Image(nii_mask.get_data(), nii_affine.affine)
        nii_rigid_mask_path = Path(tmp_folder, f'rigid_mask{Path(mask_path).name}.nii')
        nii_affine_mask_path = Path(tmp_folder, f'affine_mask{Path(mask_path).name}.nii')
        nib.save(nii_rigid_mask, nii_rigid_mask_path)
        nib.save(nii_affine_mask, nii_affine_mask_path)
        output_dict['rigid_mask'] = nii_rigid_mask_path
        output_dict['affine_mask'] = nii_affine_mask_path
        print('######################')
        print('RESLICING')
        print('######################')
        output_dict['rigid_resliced'] = engine.run_bb_spm(
            out_align['rigid'], output_dir, output_vox_size, 'resliced_')['pth']['im'][0]
        output_dict['affine_resliced'] = engine.run_bb_spm(
            out_align['affine'], output_dir, output_vox_size, 'resliced_')['pth']['im'][0]
        output_dict['rigid_resliced_mask'] = engine.run_bb_spm(
            nii_rigid_mask_path, output_dir, output_vox_size, 'resliced_')['pth']['im'][0]
        output_dict['affine_resliced_mask'] = engine.run_bb_spm(
            nii_affine_mask_path, output_dir, output_vox_size, 'resliced_')['pth']['im'][0]
    return output_dict
