from pathlib import Path
import json
import shutil
import importlib_resources as rsc

from tqdm import tqdm
import matlab.engine
from mri_preprocessing.modules import matlab_wrappers


def generate_final_preproc_dict(output_dir, final_dict_path=''):
    final_preproc_dict = {}
    if final_dict_path == '':
        final_preproc_dict_path = Path(output_dir, '__final_preproc_dict.json')
    else:
        final_preproc_dict_path = final_dict_path
    for d in tqdm(Path(output_dir).iterdir()):
        preproc_json = Path(d, '__preproc_dict.json')
        if preproc_json.is_file():
            final_preproc_dict.update(json.load(open(preproc_json, 'r')))
    with open(final_preproc_dict_path, 'w+') as out_file:
        json.dump(final_preproc_dict, out_file, indent=4)
    return final_preproc_dict


"""
We have the lesions in MNI space
We have the original images 
GOAL: get the lesions into the original space
1) compute nonlinear transformation (keeping inverse deformation field) of the b0
2) apply inverse def field to lesion
"""


def get_lesion_to_native_space(lesion_path, b0_path, output_folder):
    engine = matlab.engine.start_matlab()
    which = matlab_wrappers.matlab_check_module_path(engine, 'spm')
    spm_path = None
    if which:
        spm_path = which
    matlab_scripts_folder = rsc.files('mri_preprocessing.matlab')

    engine = matlab.engine.start_matlab()
    engine.addpath(str(matlab_scripts_folder))
    # Just in case we add all of them
    engine.addpath(spm_path)
    def_field = engine.non_linear_reg(b0_path)
    inverse_def_field = str(Path(Path(def_field).parent, 'i' + Path(def_field).name))
    output_img = engine.apply_inverse_transform(lesion_path, inverse_def_field, 'native_space_')
    output_nonlinear = str(Path(output_folder, Path(output_img).name))
    shutil.copyfile(output_img, output_nonlinear)
