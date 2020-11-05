import os
import sys
import shutil
from pathlib import Path
import importlib_resources as rsc
import argparse
import json

import matlab.engine
from mri_preprocessing.modules import preproc
pp_module_path = '/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/Patient-Preprocessing/'
sr_module_path = '/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/spm_superres/'
# pp_module_path = '/home/chrisfoulon/neuro_apps/preproc_dwi/Patient-Preprocessing/'
# sr_module_path = '/home/chrisfoulon/neuro_apps/preproc_dwi/spm_superres/'


def my_join(folder, file):
    return str(Path(folder, file))


def main():
    parser = argparse.ArgumentParser(description='Preprocess mri images')
    paths_group = parser.add_mutually_exclusive_group(required=True)
    paths_group.add_argument('-p', '--input_path', type=str, help='Root folder of the dataset')
    paths_group.add_argument('-li-', '--input_list', type=str, help='Text file containing the list of DICOM folders'
                                                                    ' containing DWI images')
    paths_group.add_argument('-d', '--input_dict', type=str, help='File path to a __dict_save json or '
                                                                  '__final_image_dict.json type file')
    parser.add_argument('-o', '--output', type=str, help='output folder')
    args = parser.parse_args()
    # TODO
    matlab_scripts_folder = rsc.files('mri_preprocessing.matlab')
    print(matlab_scripts_folder)

    engine = matlab.engine.start_matlab()
    engine.addpath(str(matlab_scripts_folder))
    engine.addpath(pp_module_path)
    engine.addpath(sr_module_path)
    """
    TESTS
    engine.run_coreg({'a': 2, 'b': 3}, 'toto')
    engine.run_coreg([1, 3, 5], 'toto')                                                                                                            
    [1]    [3]    [5]

    cell
    Out[23]: [1, 3, 5]
    for a split_dwi dict: 
    reset and denoise ALL images 
    gmean b0s and b1000s (for the denoise output) 
    rigid align b0s / affine 
    gmean b0s (rigid and affine) 
    coreg(gmean_b0, b1000s...) coreg to affine? 
    gmean b1000s gmean affine_b1000s
    non_linear_align b0
    apply transform rigid_b0 and rigid_b1000
    """
    if args.input_dict is not None:
        json_dict = Path(args.input_dict)
        if not json_dict.is_file():
            raise ValueError('{} is not an existing json'.format(json_dict))
        # json_dict = json.load(open(json_dict, 'r'))
    output_root = Path(args.output)
    if not output_root.is_dir():
        raise ValueError('{} is not an existing json'.format(output_root))
    preproc.preproc_from_dataset_dict(engine, json_dict, output_root)

    return
    # # TODO MODIFY Patient-Preprocessing/private/get_default_opt.m so the bb_spm option does not force the realign2mni
    # nii_dirs = [p for p in Path('/home/chrisfoulon/neuro_apps/data/dwi_preproc_tests/').rglob('*/split_dwi')]
    # b0_list = [p for pp in nii_dirs for p in [ip for ip in Path(pp).iterdir()] if 'bval0_' in str(p)]
    # b1000_list = [p for pp in nii_dirs for p in [ip for ip in Path(pp).iterdir()] if 'bval0_' not in str(p)]
    # for b0 in b0_list:
    #     print('STARTING PREPROC with {}'.format(b0))
    #     b0_out_dict = preproc.b0_preproc(engine, b0, args.output)
    #     # b0_out_dict = preproc.b0_preproc(engine, args.input_list, args.output)
    #     print(b0_out_dict)
