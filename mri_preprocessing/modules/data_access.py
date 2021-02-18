import json
from pathlib import Path
import shutil

import nibabel as nib
import numpy as np
from pydicom import datadict
from mri_preprocessing.modules import matlab_wrappers


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
    split_dwi_dict = {key: json_dict[key]['split_dwi'] for key in json_dict
                      if 'split_dwi' in json_dict[key] and
                      (('non_head' in json_dict[key] and json_dict[key]['non_head'] == 'False') or
                      'non_head' not in json_dict[key])}  # if non-head tag not in the dataset, we preprocess everything
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
        average_output_folder_path, '_'.join([average_method, output_type, 'b' + str(int(float(bval)))]) + '.nii')
    return average_image_list(image_list, output_path, average_method)


def generate_output_summary_old(output_root, output_folder=None):
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
        print('{} b{} images preprocessed'.format(bval_dict[bval], bval))
    return output_folder


def generate_output_summary(output_root, output_folder=None):
    output_root = Path(output_root)
    if not output_root.is_dir():
        raise ValueError('{} is not an existing directory'.format(output_root))
    if not output_folder or not Path(output_folder).is_file():
        output_folder = output_root
    matlab_wrappers.images_avg(output_root, 'rigid', 'mean', 'rigid_mean', output_folder)
    matlab_wrappers.images_avg(output_root, 'rigid', 'std', 'rigid_std', output_folder)
    matlab_wrappers.images_avg(output_root, 'affine', 'mean', 'affine_mean', output_folder)
    matlab_wrappers.images_avg(output_root, 'affine', 'std', 'affine_std', output_folder)
    matlab_wrappers.images_avg(output_root, 'nonlinear', 'mean', 'nonlinear_mean', output_folder)
    matlab_wrappers.images_avg(output_root, 'nonlinear', 'std', 'non_linear_mean', output_folder)
    return output_folder


def change_root_json_file(json_path, source_root, dest_root):
    json_path = Path(json_path)
    if json_path.is_file():
        json_dict = json.load(open(json_path, 'r'))
        for key in json_dict:
            for step in json_dict[key]:
                for bval in json_dict[key][step]:
                    json_dict[key][step][bval] = json_dict[key][step][bval].replace(
                        str(source_root), str(dest_root))
        with open(json_path, 'w+') as out_file:
            json.dump(json_dict, out_file, indent=4)


def change_root(source_root, dest_root):
    dest_root = Path(dest_root)
    source_root = Path(source_root)
    if not dest_root.is_dir():
        raise ValueError('{} is not an existing directory'.format(dest_root))
    json_path_list = [Path(d, '__preproc_dict.json') for d in dest_root.iterdir() if d.is_dir()]
    json_path_list.append(Path(dest_root, '__final_preproc_dict.json'))
    for json_path in json_path_list:
        change_root_json_file(json_path, source_root, dest_root)


def filter_out_non_head(final_preproc_dict_path, final_image_dict_path, output_folder=None):
    final_preproc_dict_path = Path(final_preproc_dict_path)
    if not final_preproc_dict_path.is_file():
        raise ValueError('{} does not exist'.format(final_preproc_dict_path))
    final_preproc_dict = json.load(open(final_preproc_dict_path, 'r'))
    final_image_dict_path = Path(final_image_dict_path)
    if not final_image_dict_path.is_file():
        raise ValueError('{} does not exist'.format(final_image_dict_path))
    final_image_dict = json.load(open(final_image_dict_path, 'r'))
    if output_folder and not Path(output_folder).is_dir():
        raise ValueError('{} is not an existing directory')
    else:
        output_folder = final_preproc_dict_path.parent
    non_head_dir = Path(output_folder, 'non_head_images')
    for key in final_preproc_dict:
        if key not in final_image_dict:
            print('{} not found in conversion output folder'.format(key))
        else:
            if 'non_head' in final_image_dict[key] and final_image_dict[key]['non_head'] == 'True':
                temp_dir_path = Path(final_preproc_dict[key]['denoise']['0.0'])
                temp_dir_parent_dir = temp_dir_path.parent
                temp_dir_name = temp_dir_parent_dir.name
                shutil.move(temp_dir_parent_dir, Path(non_head_dir, temp_dir_name))
d = {
    "DTI_65_17iso_TE85_TR14_ip3_20180403160959_6__pref__": {
        "warning": [
            "Warning: Slice timing appears corrupted (range 0..17452.5, TR=690 ms)"
        ],
        "output_dir": "/home/tolhsadum/neuro_apps/data/copy_conv/S06_DTI_65_17iso_TE85_TR14_ip3",
        "bvec": "/home/tolhsadum/neuro_apps/data/copy_conv/S06_DTI_65_17iso_TE85_TR14_ip3/DTI_65_17iso_TE85_TR14_ip3_20180403160959_6__pref__.bvec",
        "bval": "/home/tolhsadum/neuro_apps/data/copy_conv/S06_DTI_65_17iso_TE85_TR14_ip3/DTI_65_17iso_TE85_TR14_ip3_20180403160959_6__pref__.bval",
        "json": "/home/tolhsadum/neuro_apps/data/copy_conv/S06_DTI_65_17iso_TE85_TR14_ip3/DTI_65_17iso_TE85_TR14_ip3_20180403160959_6__pref__.json",
        "output_path": "/home/tolhsadum/neuro_apps/data/copy_conv/S06_DTI_65_17iso_TE85_TR14_ip3/DTI_65_17iso_TE85_TR14_ip3_20180403160959_6__pref__.nii",
        "input_folder": "/home/tolhsadum/neuro_apps/data/2018_04_03_ANALOG_44T_MRI_2018/S06_DTI_65_17iso_TE85_TR14_ip3",
        "metadata": "/home/tolhsadum/neuro_apps/data/copy_conv/S06_DTI_65_17iso_TE85_TR14_ip3/DTI_65_17iso_TE85_TR14_ip3_20180403160959_6__pref___dicom_metadata.json",
        "non_head": "False",
        "split_dwi": {
            "/home/tolhsadum/neuro_apps/data/copy_conv/S06_DTI_65_17iso_TE85_TR14_ip3/split_dwi/DTI_65_17iso_TE85_TR14_ip3_20180403160959_6__pref___bval0_vol0.nii": 0.0,
            "/home/tolhsadum/neuro_apps/data/copy_conv/S06_DTI_65_17iso_TE85_TR14_ip3/split_dwi/DTI_65_17iso_TE85_TR14_ip3_20180403160959_6__pref___bval1485_vol1.nii": 1485.0,
        }
    }
}


def create_pseudo_input_dict(root_directory, add_non_head_tag=True):
    """

    Parameters
    ----------
    root_directory: pathlike
    add_non_head_tag: bool
        If True, adds a non_head tag to all entries set to False (meaning it's considered a head)

    Returns
    -------

    """
    if not Path(root_directory).is_dir():
        raise ValueError('{} is not an existing directory'.format(root_directory))
    output_dict_path = Path(root_directory, '__pseudo_final_dict.json')
    final_dict = {}
    for directory in [d for d in Path(root_directory).rglob('*') if d.is_dir()]:
        nii_list = [nii for nii in directory.iterdir() if nii.is_file() and (
                nii.name.endswith('nii') or nii.name.endswith('nii.gz'))]
        if len(nii_list) > 2:
            raise ValueError('{} contains more than 2 nifti images'.format(directory))
        b0 = None
        b1000 = None
        for nii in nii_list:
            if 'b0' in nii.name and 'b1000' not in nii.name:
                b0 = str(nii)
            if 'b1000' in nii.name and 'b0' not in nii.name:
                b1000 = str(nii)
        if b0 is None or b1000 is None:
            raise ValueError('Cannot find out which file is a b0 and which is the b1000 in {}'.format(directory))
        # If we are here we should have a b0 and a b1000 so we can create the dictionary entry
        final_dict[directory.name] = {
            "output_dir": str(directory),
            "output_path": b0,
            "non_head": "False",
            "split_dwi": {
                b0: 0.0,
                b1000: 1000.0,
            }
        }
    with open(output_dict_path, 'w+') as out_file:
        json.dump(final_dict, out_file, indent=4)
    return output_dict_path
