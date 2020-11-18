import json
from pathlib import Path

import nibabel as nib
import numpy as np
from pydicom import datadict


output_filename_patterns = {
    'denoise': 'geomean_denoise_',
    'rigid': 'resliced_co-rigid_rigid_geomean_denoise_',
    'affine': 'resliced_co-affine_affine_geomean_denoise_',
    'non-linear': 'non_linear_co-rigid_rigid_geomean_denoise_',
    'def-field': 'y_co-rigid_rigid_geomean_denoise_'
}


def get_attr_from_metadata_dict(metadata_dict, attribute):
    tag = format(datadict.tag_for_keyword(attribute), '08x').upper()
    if tag in metadata_dict:
        return metadata_dict[tag]
    else:
        return None


def get_attr_from_metadata_json(metadata_json, attribute):
    if not Path(metadata_json).is_file():
        raise ValueError('{} is not an existing metadata file'.format(metadata_json))
    return get_attr_from_metadata_dict(json.load(open(metadata_json, 'r')), attribute)


def get_attr_from_output_subdict(output_subdict, attribute):
    if 'metadata' in output_subdict:
        return get_attr_from_metadata_json(output_subdict['metadata'], attribute)
    else:
        raise ValueError('the output subdictionary does not contain a metadata file path')


def get_attr_from_output_dict_key(output_dict, key, attribute):
    if key not in output_dict:
        raise ValueError('{} not in output_dict'.format(key))
    return get_attr_from_output_subdict(output_dict[key], attribute)


def get_dwi_lists_from_dict(split_dwi_dict):
    b0_list = [path for path in split_dwi_dict if split_dwi_dict[path] == 0.0]
    b1000_list = [path for path in split_dwi_dict if split_dwi_dict[path] != 0.0]
    return b0_list, b1000_list


def get_split_dict_from_json(json_path):
    json_path = Path(json_path)
    if not json_path.is_file():
        raise ValueError('{} does not exist'.format(json_path))
    json_dict = json.load(open(json_path, 'r'))
    split_dwi_dict = {key: json_dict[key]['split_dwi'] for key in json_dict if 'split_dwi' in json_dict[key]}
    return split_dwi_dict


def check_series(json_path):
    json_dict = json.load(open(json_path, 'r'))
    split_dwi_dict = get_split_dict_from_json(json_path)
    singleton_key_list = [s for s in split_dwi_dict if len(split_dwi_dict[s]) == 1]
    non_singleton_key_list = [s for s in split_dwi_dict if len(split_dwi_dict[s]) > 1]
    series_dict = {get_attr_from_output_dict_key(
        json_dict, key, 'StudyInstanceUID')['Value'][0]: key for key in non_singleton_key_list}
    real_singletons_list = [
        k for k in singleton_key_list if get_attr_from_output_dict_key(
            json_dict, k, 'StudyInstanceUID')['Value'][0] not in series_dict]
    return real_singletons_list


def check_output_integrity(output_folder):
    json_file = Path(output_folder, '__preproc_dict.json')
    if not json_file.is_file():
        print('INTEGRITY ERROR : [{}] Cannot find json'.format(json_file))
        return False

    json_dict = json.load(open(json_file, 'r'))
    if not json_dict:
        print('INTEGRITY ERROR : [{}] Cannot open json'.format(json_file))
        return False
    # There should always be only one key but it doesn't matter
    for key in json_dict:
        for output in json_dict[key]:
            for bval in json_dict[key][output]:
                path = json_dict[key][output][bval]
                if not Path(path).is_file():
                    print('INTEGRITY ERROR : [{}] does not exist'.format(path))
                    return False
    return True


def average_image_list(images_list, output_path, average_method):
    nii_list = [nib.load(path) for path in images_list]

    average_image = getattr(np, average_method, None)(
        np.stack(np.array([nii.get_fdata() for nii in nii_list]), axis=3), axis=3)
    if average_image is None:
        raise ValueError('{} is not an existing numpy function'.format(average_method))
    nib.save(nib.Nifti1Image(average_image, nii_list[0].affine), output_path)
    return output_path


def create_output_average_old(output_root, output_path, filename_pattern, average_method='mean'):
    """

    Parameters
    ----------
    output_path
    output_root
    filename_pattern
        e.g. '*resliced_co-affine_rigid_denoise*__pref___bval0.nii'
    average_method

    Returns
    -------

    """
    output_root = Path(output_root)
    if not output_root.is_dir():
        raise ValueError('{} is not an existing directory'.format(output_root))
    images_list = [ff for d in output_root.iterdir() if d.is_dir() for ff in d.glob(filename_pattern)]

    return average_image_list(images_list, output_path, average_method)


def create_output_average(output_root, average_output_folder_path, output_type, bval, average_method='mean'):
    output_root = Path(output_root)
    if not output_root.is_dir():
        raise ValueError('{} is not an existing directory'.format(output_root))
    final_json = Path(output_root, '__final_preproc_dict.json')
    if final_json.is_file():
        with open(final_json, 'r') as jfile:
            output_dict = json.load(jfile)
    else:
        output_dict = {}
        for subfolder in output_root.iterdir():
            if check_output_integrity(subfolder):
                output_dict.update(json.load(Path(subfolder, '__preproc_dict.json')))
    image_list = []
    for key in output_dict:
        if output_type in output_dict[key]:
            if bval in output_dict[key][output_type]:
                if Path(output_dict[key][output_type][bval]).is_file():
                    image_list.append(output_dict[key][output_type][bval])
    output_path = Path(
        average_output_folder_path, '_'.join([average_method, output_type, str(int(float(bval)))]) + '.nii')
    return average_image_list(image_list, output_path, average_method)


def generate_output_summary(output_root, output_folder=None):
    output_root = Path(output_root)
    if not output_root.is_dir():
        raise ValueError('{} is not an existing directory'.format(output_root))
    if not output_folder or not Path(output_folder).is_file():
        output_folder = output_root
    final_dict = json.load(open(Path(output_root, '__final_preproc_dict.json')))
    bval_dict = {}
    for key in final_dict:
        for bval in final_dict[key]['denoise']:
            if bval in bval_dict:
                bval_dict[bval] += 1
            else:
                bval_dict[bval] = 1

    print('######## OUTPUT SUMMARY DWI PREPROC #######')
    print('Output root directory: {}'.format(output_root))
    print('{} output sub-folders'.format(len(final_dict)))
    print('Average images created in {}'.format(output_folder))
    for bval in bval_dict:
        mean_rigid = create_output_average(output_root, output_folder, 'rigid', bval, 'mean')
        std_rigid = create_output_average(output_root, output_folder, 'rigid', bval, 'std')
        mean_affine = create_output_average(output_root, output_folder, 'affine', bval, 'mean')
        std_affine = create_output_average(output_root, output_folder, 'affine', bval, 'std')
        mean_nonlinear = create_output_average(output_root, output_folder, 'nonlinear', bval, 'mean')
        std_nonlinear = create_output_average(output_root, output_folder, 'nonlinear', bval, 'std')
        print('{} b{} images preprocessed'.format(len(bval_dict[bval]), bval))
    return output_folder
