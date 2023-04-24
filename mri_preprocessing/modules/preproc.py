import shutil
from pathlib import Path
import os
import time
import json
import importlib_resources as rsc

import matlab.engine
from multiprocessing.dummy import Pool as ThreadPool
import multiprocessing
import nibabel as nib
from scipy.stats import gmean
import numpy as np
from mri_preprocessing.modules import data_access, matlab_wrappers

spm_path = ''
superres_path = ''
patient_preproc_path = ''


def check_spm_modules():
    engine = matlab.engine.start_matlab()
    which = matlab_wrappers.matlab_check_module_path(engine, 'spm')
    if which:
        global spm_path
        spm_path = which
    which = matlab_wrappers.matlab_check_module_path(engine, 'spm_superres')
    if which:
        global superres_path
        superres_path = which
    which = matlab_wrappers.matlab_check_module_path(engine, 'RunPreproc')
    if which:
        global patient_preproc_path
        patient_preproc_path = which


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
            return str(output_path)
        else:
            shutil.copyfile(Path(nii_array[0]), output_path)
            return str(output_path)
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


def dwi_preproc_dict(engine, split_dict, output_folder, output_vox_size=2):
    """

       for a split_dwi dict: (we can create the key{nii:bval} dict and just give the dict
       and the key to dwi_preproc_dict)
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

    if 0 not in b_dict or len(b_dict) == 1:
        print('B0 NOT FOUND IN {} OR ONLY CONTAINS ONE DWI THE FOLDER WILL THEN BE IGNORED')
        shutil.rmtree(output_folder)
        return {}
    print('######################')
    print('RESET ORIGIN AND GEOMEAN')
    print('######################')
    b_denoised_dict = {}
    for b in b_dict:
        b_list = []
        for img_path in b_dict[b]:
            output_reset = matlab_wrappers.reset_orient_mat(engine, img_path, Path(tmp_folder))
            b_list.append(output_reset)
            # output_reset = matlab_wrappers.reset_orient_mat(engine, img_path, Path(tmp_folder, Path(img_path).name))
            # out_denoise_test = Path(tmp_folder, 'denoise_' + Path(img_path).name)
            # # Disabling the denoising as it takes too much time and might be unnecessary
            # if False and not out_denoise_test.is_file():
            #     output_denoise = engine.run_denoise(output_reset, tmp_folder, 'denoise_')['pth']['im'][0]
            #     b_list.append(output_denoise)
            # else:
            #     b_list.append(str(out_denoise_test))
        b_denoised_dict[b] = nii_gmean(b_list, str(Path(output_folder, 'geomean_' +
                                                        format_filename(Path(b_list[0]).name, int(round(b))))))
        # now b_dict contains the denoised images (maybe not used later)
        b_dict[b] = b_list

    print('######################')
    print('RIGID AND AFFINE ALIGNMENT OF THE GEOMEAN IMAGES')
    print('######################')
    rigid_aligned_dict = {}
    affine_aligned_dict = {}
    for bval in b_denoised_dict:
        out_align = engine.my_align(b_denoised_dict[bval], tmp_folder)
        rigid_aligned_dict[bval] = out_align['rigid']
        affine_aligned_dict[bval] = out_align['affine']

    print('######################')
    print('COREG OF THE B1000s TO THE B0')
    print('######################')
    bval_list = [0] + [k for k in rigid_aligned_dict if k != 0]
    denoised_rigid_images_list = [rigid_aligned_dict[k] for k in bval_list]
    denoised_affine_images_list = [affine_aligned_dict[k] for k in bval_list]
    co_rigid_aligned_list = engine.run_coreg(denoised_rigid_images_list, tmp_folder, 'co-rigid_')['pth']['im']
    co_affine_aligned_list = engine.run_coreg(denoised_affine_images_list, tmp_folder, 'co-affine_')['pth']['im']
    for ind, bval in enumerate(bval_list):
        rigid_aligned_dict[bval] = co_rigid_aligned_list[ind]
        affine_aligned_dict[bval] = co_affine_aligned_list[ind]
    print('######################')
    print('RESLICING')
    print('######################')
    resliced_rigid_dict = {}
    resliced_affine_dict = {}
    for bval in rigid_aligned_dict:
        resliced_rigid_dict[bval] = engine.run_bb_spm(
            rigid_aligned_dict[bval], output_folder, output_vox_size, 'resliced_')['pth']['im'][0]
        resliced_affine_dict[bval] = engine.run_bb_spm(
            affine_aligned_dict[bval], output_folder, output_vox_size, 'resliced_')['pth']['im'][0]

    non_linear_dict = {}
    def_field_dict = {}
    inv_def_field_dict = {}
    # if 0 in rigid_aligned_dict:
    print('######################')
    print('NONLINEAR REG B0 (DEFORMATION FIELD CALCULATION)')
    print('######################')
    # As we use the b0 to MNI transform to register the other bvalues to the MNI, we just need one def field and inverse
    def_field = engine.non_linear_reg(rigid_aligned_dict[0])
    inverse_def_field = str(Path(Path(def_field).parent, 'i' + Path(def_field).name))
    print('######################')
    print('APPLY NON-LINEAR + RESLICE')
    print('######################')
    for bval in rigid_aligned_dict:
        def_field_dict[bval] = def_field
        inv_def_field_dict[bval] = inverse_def_field
        output_img = engine.apply_transform(rigid_aligned_dict[bval], def_field_dict[0], output_vox_size)
        output_nonlinear = str(Path(output_folder, Path(output_img).name))
        shutil.copyfile(output_img, output_nonlinear)
        non_linear_dict[bval] = output_nonlinear

    output_dict = {
        'denoise': b_denoised_dict,
        'rigid': resliced_rigid_dict,
        'affine': resliced_affine_dict,
        'nonlinear': non_linear_dict,
        'def_field': def_field_dict,
        'inv_def_field': inv_def_field_dict,
    }
    return output_dict


def partial_preproc_from_dataset_dict(split_dwi_dict, key, output_root, rerun_strat='resume', output_vox_size=2):
    try:
        output_dir = Path(output_root, key)
        if output_dir.is_dir():
            if rerun_strat == 'delete':
                for i in range(5):
                    try:
                        shutil.rmtree(output_dir)
                    except OSError as e:
                        print('Could not delete {}, still trying to preprocess but please verify the output'.format(
                            output_dir))
                        print(e)
                        time.sleep(5)
            if rerun_strat == 'resume':
                integrity = data_access.check_output_integrity(output_dir)
                if integrity:
                    print('{} has already been preprocessed it will then be skipped'.format(output_dir))
                    return json.load(open(Path(output_dir, '__preproc_dict.json'), 'r'))
                else:
                    print('Integrity check in {} detected an error, '
                          'the folder is then erased and preprocessed again'.format(output_dir))
                    for i in range(5):
                        try:
                            shutil.rmtree(output_dir)
                        except OSError as e:
                            print('Could not delete {}, still trying to preprocess but please verify the output'.format(
                                output_dir))
                            print(e)
                            time.sleep(5)
        matlab_scripts_folder = rsc.files('mri_preprocessing.matlab')

        engine = matlab.engine.start_matlab()
        engine.addpath(str(matlab_scripts_folder))
        # Just in case we add all of them
        engine.addpath(spm_path)
        engine.addpath(superres_path)
        engine.addpath(patient_preproc_path)
        engine.cd(patient_preproc_path + '/private')
        os.makedirs(output_dir, exist_ok=True)
        b_dict = dwi_preproc_dict(engine, split_dwi_dict[key], output_dir, output_vox_size)
        if not b_dict:
            return {}
        save_dict = {key: b_dict}
        with open(Path(output_dir, '__preproc_dict.json'), 'w+') as out_file:
            json.dump(save_dict, out_file, indent=4)
            print(f'Preprocessed folder, dictionary saved at {Path(output_dir, "__preproc_dict.json")}')
        return save_dict
    except Exception as e:
        error_dir = Path(output_root, 'errors')
        if not error_dir.is_dir():
            error_dir.mkdir()
        output_error_path = Path(error_dir, key + '_error.txt')
        output_error_path.write_text('ERROR WITH KEY [{}]:\n{}'.format(key, e))
        return {}


def preproc_from_dataset_dict(json_path, output_root, rerun_strat='resume', nb_cores=1, output_vox_size=2,
                              pair_singletons=True):
    split_dwi_dict = data_access.get_split_dict_from_json(json_path)
    # both keys having the same preproc output
    check_spm_modules()
    if not all([spm_path, superres_path, patient_preproc_path]):
        print('Missing matlab modules (spm, spm_superres and Patient-Preprocessing (RunPreproc) are required)'
              '\n https://www.fil.ion.ucl.ac.uk/spm/'
              '\n https://github.com/brudfors/spm_superres'
              '\n https://github.com/WTCN-computational-anatomy-group/Patient-Preprocessing')
        exit()
    if pair_singletons:
        json_path = Path(json_path)
        if not json_path.is_file():
            raise ValueError('{} does not exist'.format(json_path))
        json_dict = json.load(open(json_path, 'r'))
        # List split dwi with only one volume
        singleton_key_list = [s for s in split_dwi_dict if len(split_dwi_dict[s]) == 1]
        # Separate the correctly formed dwi
        non_singleton_key_list = [s for s in split_dwi_dict if len(split_dwi_dict[s]) > 1]
        # List the series number of every correctly formed split dwi
        series_dict = {data_access.get_attr_from_output_dict_key(
            json_dict, key, 'StudyInstanceUID')['Value'][0]: key for key in non_singleton_key_list}
        # Filter out the singletons with the same series as a correctly formed split dwi
        matched_singeltons = {}
        for key in singleton_key_list:
            series = data_access.get_attr_from_output_dict_key(json_dict, key, 'StudyInstanceUID')['Value'][0]
            if series not in series_dict:
                if series not in matched_singeltons:
                    matched_singeltons[series] = [key]
                else:
                    matched_singeltons[series].append(key)
        # If the singletons cannot be matched with any other dwi we ignore them as we don't know what to do with it.
        matched_split_dwi = {}
        for series in list(matched_singeltons):
            if len(matched_singeltons[series]) == 1:
                del matched_singeltons[series]
            else:
                # We create merged split_dwi dictionaries associated with the common series of the singletons
                matched_split_dwi[matched_singeltons[series][0]] = {}
                for key in matched_singeltons[series]:
                    matched_split_dwi[matched_singeltons[series][0]].update(split_dwi_dict[key])
        # Now we create the curated split_dwi_dict
        new_split_dwi = {}
        for key in non_singleton_key_list:
            new_split_dwi[key] = split_dwi_dict[key]
        new_split_dwi.update(matched_split_dwi)
        split_dwi_dict = new_split_dwi
    else:
        split_dwi_dict = {k: split_dwi_dict[k] for k in split_dwi_dict if len(split_dwi_dict[k]) >= 1}

    keys_list = [k for k in split_dwi_dict]
    if nb_cores != 1:
        if nb_cores == -1:
            nb_cores = multiprocessing.cpu_count()
        pool = ThreadPool(nb_cores)
        list_of_output_dict = pool.map(
            lambda key: partial_preproc_from_dataset_dict(
                split_dwi_dict, key, output_root, rerun_strat, output_vox_size), keys_list)

        pool.close()
        pool.join()
    else:
        list_of_output_dict = []
        for k in keys_list:
            list_of_output_dict.append(
                partial_preproc_from_dataset_dict(split_dwi_dict, k, output_root, rerun_strat, output_vox_size))
    # for key in split_dwi_dict:
    #     # TODO maybe make a rerun strategy mechanism
    #     output_dir = Path(output_root, key)
    #     os.makedirs(output_dir, exist_ok=True)
    #     b_dict = dwi_preproc_dict(engine, split_dwi_dict[key], output_dir)
    #     output_dict[key] = b_dict

    output_dict = {}
    for d in list_of_output_dict:
        output_dict.update(d)
    if pair_singletons:
        # We duplicate the preproc output for the singletons to match with the keys of the conversion pipeline output
        for key in matched_split_dwi:
            if key in output_dict:
                for matched_key in matched_split_dwi[key]:
                    output_dict[matched_key] = output_dict[key]
                del output_dict[key]
    return output_dict
