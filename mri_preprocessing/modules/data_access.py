import json
from pathlib import Path

import nibabel as nib
import numpy as np
from pydicom import datadict


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
        json_dict, key, 'StudyInstanceUID')['Value']: key for key in non_singleton_key_list}
    real_singletons_list = [
        k for k in singleton_key_list if get_attr_from_output_dict_key(
            json_dict, k, 'StudyInstanceUID')['Value'] not in series_dict]
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


def create_output_average(output_root, output_path, filename_pattern, average_method='mean'):
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
    # images_list = [f for f in output_root.iterdir(filename_pattern) if f.is_dir()]
    nii_list = [nib.load(path) for path in images_list]

    average_image = getattr(np, average_method, None)(
        np.stack(np.array([nii.get_fdata() for nii in nii_list]), axis=3), axis=3)
    if average_image is None:
        raise ValueError('{} is not an existing numpy function'.format(average_method))
    nib.save(nib.Nifti1Image(average_image, nii_list[0].affine), output_path)
    return output_path
