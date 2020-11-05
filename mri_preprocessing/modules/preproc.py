import shutil
from pathlib import Path
import os

import nibabel as nib
from scipy.stats import gmean
import numpy as np
from mri_preprocessing.modules import data_access, matlab_wrappers

""" Matlab modules management: store the path to the local matlab modules somewhere in the package install. 
The first time the scripts are used, check if the matlab paths have been setup, if not, ask if you want to set them up.
"""

# pp_module_path = '/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/Patient-Preprocessing/'
# sr_module_path = '/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/spm_superres/'


def my_join(folder, file):
    return str(Path(folder, file))


def format_filename(filename, bval):
    if 'bval' in filename:
        return filename.split('bval')[0] + 'bval{}.nii'.format(int(round(bval)))
    else:
        return filename.split('.nii')[0] + 'bval{}.nii'.format(int(round(bval)))


# TODO IMPORTANT we want to gmean only the images with THE SAME BVAL
def nii_gmean(nii_array, output_path):
    """
    IMPORTANT: the images affine must be the same as the output affine will be taken only from the first image
    Parameters
    ----------
    nii_array : arraylike of nibabel.Nifti1Image or arraylike of image paths
    output_path : str
        path to the output image (will be created / overwritten)
    Returns
    -------
        output_path : str
            if nii_array contained only one image, this image will simply be copied in output_path
    """
    if len(nii_array) == 1:
        if isinstance(nii_array, nib.Nifti1Image):
            shutil.copyfile(nii_array[0].get_filename(), output_path)
            return output_path
        else:
            shutil.copyfile(Path(nii_array[0]), output_path)
            return output_path
    for ind, n in enumerate(nii_array):
        if not isinstance(n, nib.Nifti1Image):
            p = Path(n)
            if p.is_file():
                nii_array[ind] = nib.load(p)
            else:
                raise ValueError('The array must contain either existing file paths or nibabel.Nifti1Image objects')
    data = np.stack(np.array([nii.get_fdata() for nii in nii_array]), axis=3)

    gmeaned = gmean(data, axis=3)
    output_path = Path(output_path).absolute()
    nib.save(nib.Nifti1Image(gmeaned, nii_array[0].affine), output_path)
    return str(output_path)


def b0_preproc(engine, img_path, output_folder):
    # engine.addpath(pp_module_path)
    # engine.addpath(sr_module_path)
    input_file = Path(img_path)
    input_basename = input_file.name
    denoise_basename = 'denoise_' + input_basename
    # nonlinear_basename = 'nonlinear_' + input_basename
    # Everything has to be a string otherwise matlab explodes because it's the best language ever
    output_folder = Path(output_folder)
    if not Path.is_dir(output_folder):
        os.makedirs(output_folder)
    output_folder = str(output_folder)
    tmp_folder = str(Path(output_folder, 'tmp'))
    if not os.path.isdir(tmp_folder):
        os.makedirs(tmp_folder)
    # preproc_image_path = os.path.join(output_folder, os.path.basename(input_file))
    tmp_image_path = str(Path(tmp_folder, input_basename))
    shutil.copyfile(str(input_file), tmp_image_path)

    print('######################')
    print('RESET ORIGIN')
    print('######################')
    engine.reset_orient_mat(str(tmp_image_path), nargout=0)
    tmp_denoise = my_join(tmp_folder, denoise_basename)
    shutil.copyfile(tmp_image_path, tmp_denoise)
    print('######################')
    print('DENOISING')
    print('######################')
    out_denoise = engine.run_denoise(tmp_denoise, output_folder)['pth']['im'][0]
    # Will be created by run_denoise (RunPreproc call)
    # out_denoise = my_join(output_folder, denoise_basename)
    print('######################')
    print('RIGID AND AFFINE ALIGNMENT TO MNI')
    print('######################')
    out_align = engine.my_align(out_denoise, tmp_folder)
    tmp_rigid = out_align['rigid']
    tmp_affine = out_align['affine']
    print('######################')
    print('APPLY RIGID + RESLICE')
    print('######################')
    out_rigid = engine.run_bb_spm(tmp_rigid, output_folder, 2)['pth']['im'][0]

    print('######################')
    print('APPLY AFFINE + RESLICE')
    print('######################')
    out_affine = engine.run_bb_spm(tmp_affine, output_folder, 2)['pth']['im'][0]

    print('######################')
    print('NON-LINEAR ALIGNMENT TO MNI')
    print('######################')
    def_field = engine.non_linear_reg(tmp_rigid)
    print('######################')
    print('APPLY NON-LINEAR + RESLICE')
    print('######################')
    output_img = engine.apply_transform(tmp_rigid)
    output_nonlinear = my_join(output_folder, Path(output_img).name)
    shutil.copyfile(tmp_rigid, output_nonlinear)
    output_dict = {
        'denoise': out_denoise,
        'rigid': out_rigid,
        'affine': out_affine,
        'nonlinear': output_nonlinear,
        'def_field': def_field
    }
    return output_dict


def b1000_preproc(engine, img_path, output_folder, def_field):
    """"""
    input_file = Path(img_path)
    input_basename = input_file.name
    denoise_basename = 'denoise_' + input_basename
    # nonlinear_basename = 'nonlinear_' + input_basename
    # Everything has to be a string otherwise matlab explodes because it's the best language ever
    output_folder = Path(output_folder)
    if not Path.is_dir(output_folder):
        os.makedirs(output_folder)
    output_folder = str(output_folder)
    tmp_folder = str(Path(output_folder, 'tmp'))
    if not os.path.isdir(tmp_folder):
        os.makedirs(tmp_folder)
    # preproc_image_path = os.path.join(output_folder, os.path.basename(input_file))
    tmp_image_path = str(Path(tmp_folder, input_basename))
    shutil.copyfile(str(input_file), tmp_image_path)

    print('######################')
    print('RESET ORIGIN')
    print('######################')
    engine.reset_orient_mat(str(tmp_image_path), nargout=0)
    tmp_denoise = my_join(tmp_folder, denoise_basename)
    # output_nonlinear = my_join(output_folder, nonlinear_basename)
    shutil.copyfile(tmp_image_path, tmp_denoise)
    print('######################')
    print('DENOISING')
    print('######################')
    out_denoise = engine.run_denoise(tmp_denoise, output_folder)['pth']['im'][0]
    # Will be created by run_denoise (RunPreproc call)
    # out_denoise = my_join(output_folder, denoise_basename)
    print('######################')
    print('RIGID AND AFFINE ALIGNMENT TO MNI')
    print('######################')
    out_align = engine.my_align(out_denoise, tmp_folder)
    tmp_rigid = out_align['rigid']
    tmp_affine = out_align['affine']
    print('######################')
    print('APPLY RIGID + RESLICE')
    print('######################')
    out_rigid = engine.run_bb_spm(tmp_rigid, output_folder, 2)['pth']['im'][0]

    print('######################')
    print('APPLY AFFINE + RESLICE')
    print('######################')
    out_affine = engine.run_bb_spm(tmp_affine, output_folder, 2)['pth']['im'][0]

    print('######################')
    print('APPLY NON-LINEAR + RESLICE')
    print('######################')
    output_img = engine.apply_transform(tmp_rigid)
    output_nonlinear = my_join(output_folder, Path(output_img).name)
    shutil.copyfile(tmp_rigid, output_nonlinear)
    output_dict = {
        'denoise': out_denoise,
        'rigid': out_rigid,
        'affine': out_affine,
        'nonlinear': output_nonlinear,
        'def_field': def_field
    }
    return output_dict


def preproc_folder(b0_list, b1000_list, output_folder):
    """

    Parameters
    ----------
    b0_list
    b1000_list
    output_folder

    Returns
    -------
    Notes
    -----
    1) denoise all the images
    2) rigid align all the images
    """
    if isinstance(b0_list, list):
        return  # average the images into one
    return


def dwi_preproc_dict(engine, split_dict, output_folder):
    """

       for a split_dwi dict: (we can create the key{nii:bval} dict and just give the dict and the key to dwi_preproc_dict)
       reset and denoise ALL images
       gmean b0s and b1000s (from the denoise output)
       rigid align b0s / affine
       gmean b0s (rigid and affine)
       coreg(gmean_b0, b1000s...) coreg to affine?
       run_bb gmeaned rigid and affine (output)
       gmean b1000s gmean affine_b1000s
       non_linear_align b0
       apply transform rigid_b0 and rigid_b1000
       """
    output_folder = Path(output_folder)
    if not Path.is_dir(output_folder):
        os.makedirs(output_folder)
    output_folder = str(output_folder)
    tmp_folder = str(Path(output_folder, 'tmp'))
    if not os.path.isdir(tmp_folder):
        os.makedirs(tmp_folder)
    b_dict = {}
    for b in split_dict:
        bval = split_dict[b]
        if bval not in b_dict:
            b_dict[bval] = [b]
        else:
            b_dict[bval].append(b)
    print('######################')
    print('RESET ORIGIN, DENOISING AND GEOMEAN')
    print('######################')
    b_denoised_dict = {}
    for b in b_dict:
        b_list = []
        for img_path in b_dict[b]:
            output_reset = matlab_wrappers.reset_orient_mat(engine, img_path, Path(tmp_folder, Path(img_path).name))
            out_denoise_test = Path(tmp_folder, 'denoise_' + Path(img_path).name)
            if not out_denoise_test.is_file():
                output_denoise = engine.run_denoise(output_reset, tmp_folder, 'denoise_')['pth']['im'][0]
                b_list.append(output_denoise)
            else:
                b_list.append(str(out_denoise_test))
        b_denoised_dict[b] = nii_gmean(b_list, Path(output_folder,
                                                    format_filename(Path(b_list[0]).name, int(round(b)))))
        # now b_dict contains the denoised images (maybe not used later)
        b_dict[b] = b_list

    # b0_align_dict = {'rigid': [], 'affine': []}
    # if 0 in b_denoised_dict:
    #     b0_align_dict = {'rigid': [], 'affine': []}
    #     for b0 in b_denoised_dict[0]:
    #         out_align = engine.my_align(b0, tmp_folder)
    #         b0_align_dict['rigid'].append(out_align['rigid'])
    #         b0_align_dict['affine'].append(out_align['affine'])
    print('######################')
    print('COREG OF THE B1000s TO THE B0')
    print('######################')
    rigid_aligned_dict = {}
    affine_aligned_dict = {}
    if 0 in b_denoised_dict:
        print('######################')
        print('B0 RIGID AND AFFINE ALIGNMENT')
        print('######################')
        out_align = engine.my_align(b_denoised_dict[0], tmp_folder)
        rigid_aligned_dict[0] = out_align['rigid']
        affine_aligned_dict[0] = out_align['affine']
        for bval in b_denoised_dict:
            if bval != 0.0:
                # the first output image is the b0 used as a reference images for the coreg
                rigid_aligned_dict[bval] = engine.run_coreg(
                    [rigid_aligned_dict[0], b_denoised_dict[bval]], tmp_folder, 'co-rigid_')['pth']['im'][1]
                affine_aligned_dict[bval] = engine.run_coreg(
                    [affine_aligned_dict[0], b_denoised_dict[bval]], tmp_folder, 'co-affine_')['pth']['im'][1]
    else:
        for bval in b_denoised_dict:
            out_align = engine.my_align(b_denoised_dict[bval], tmp_folder)
            rigid_aligned_dict[bval] = out_align['rigid']
            affine_aligned_dict[bval] = out_align['affine']
    print('######################')
    print('RESLICING')
    print('######################')
    resliced_rigid_dict = {}
    resliced_affine_dict = {}
    for bval in rigid_aligned_dict:
        resliced_rigid_dict[bval] = engine.run_bb_spm(
            rigid_aligned_dict[bval], output_folder, 2, 'resliced_')['pth']['im'][0]
        resliced_affine_dict[bval] = engine.run_bb_spm(
            affine_aligned_dict[bval], output_folder, 2, 'resliced_')['pth']['im'][0]

    non_linear_dict = {}
    def_field_dict = {}
    if 0 in rigid_aligned_dict:
        print('######################')
        print('NONLINEAR REG B0 (DEFORMATION FIELD CALCULATION)')
        print('######################')
        def_field_dict[0] = engine.non_linear_reg(rigid_aligned_dict[0])
        print('######################')
        print('APPLY NON-LINEAR + RESLICE')
        print('######################')
        for bval in rigid_aligned_dict:
            def_field_dict[bval] = def_field_dict[0]
            output_img = engine.apply_transform(rigid_aligned_dict[bval], def_field_dict[0])
            output_nonlinear = my_join(output_folder, Path(output_img).name)
            shutil.copyfile(rigid_aligned_dict[bval], output_nonlinear)
            non_linear_dict[bval] = output_nonlinear
    else:
        for bval in rigid_aligned_dict:
            print('######################')
            print('NONLINEAR REG')
            print('######################')
            def_field_dict[bval] = engine.non_linear_reg(rigid_aligned_dict[0])
            print('######################')
            print('APPLY NON-LINEAR + RESLICE')
            print('######################')
            output_img = engine.apply_transform(rigid_aligned_dict[bval], def_field_dict[bval])
            output_nonlinear = my_join(output_folder, Path(output_img).name)
            shutil.copyfile(rigid_aligned_dict[bval], output_nonlinear)
            non_linear_dict[bval] = output_nonlinear

    output_dict = {
        'denoise': b_denoised_dict,
        'rigid': resliced_rigid_dict,
        'affine': resliced_affine_dict,
        'nonlinear': non_linear_dict,
        'def_field': def_field_dict
    }
    print(output_dict)

    return output_dict


def preproc_from_dataset_dict(engine, json_path, output_root):
    split_dwi_dict = data_access.get_split_dict_from_json(json_path)
    output_dict = {}
    for key in split_dwi_dict:
        # TODO maybe make a rerun strategy mechanism
        output_dir = Path(output_root, key)
        os.makedirs(output_dir, exist_ok=True)
        b_dict = dwi_preproc_dict(engine, split_dwi_dict[key], output_dir)
        # output_dict[key] = {'b0': b0_preproc_dict, 'b1000': b1000_preproc_dict}
    return output_dict
