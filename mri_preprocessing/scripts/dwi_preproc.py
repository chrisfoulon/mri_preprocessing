import os
import sys
import shutil
from pathlib import Path
import importlib_resources as rsc
import argparse

import matlab.engine
from mri_preprocessing.modules import preproc
pp_module_path = '/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/Patient-Preprocessing/'
sr_module_path = '/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/spm_superres/'


def my_join(folder, file):
    return str(Path(folder, file))


def main():
    parser = argparse.ArgumentParser(description='Preprocess mri images')
    paths_group = parser.add_mutually_exclusive_group(required=True)
    paths_group.add_argument('-p', '--input_path', type=str, help='Root folder of the dataset')
    paths_group.add_argument('-li-', '--input_list', type=str, help='Text file containing the list of DICOM folders'
                                                                    ' containing DWI images')
    parser.add_argument('-o', '--output', type=str, help='output folder')
    args = parser.parse_args()
    # TODO
    matlab_scripts_folder = rsc.files('mri_preprocessing.matlab')
    print(matlab_scripts_folder)

    engine = matlab.engine.start_matlab()
    engine.addpath(str(matlab_scripts_folder))
    engine.addpath(pp_module_path)
    engine.addpath(sr_module_path)
    print('STARTING PREPROC')
    b0_out_dict = preproc.b0_preproc(engine, args.input_list, args.output)
    print(b0_out_dict)
