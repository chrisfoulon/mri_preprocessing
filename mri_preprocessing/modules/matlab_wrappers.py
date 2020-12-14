from pathlib import Path
import shutil
import os
import json
import importlib_resources as rsc

import matlab.engine


def reset_orient_mat(engine, img_path, output):
    img_path = Path(img_path)
    if not img_path.is_file():
        raise ValueError('{} does not exist'.format(img_path))
    output = Path(output)
    if output.is_dir():
        output_path = Path(output, img_path.name)
        if output_path == img_path:
            output_path = Path(output, 'reset_' + img_path.name)
    else:
        output_path = output
    shutil.copyfile(img_path, output_path)
    engine.reset_orient_mat(str(output_path), nargout=0)
    return str(output_path)


# not used anymore as the matlab scripts have been fixed
def run_denoise(engine, img_path, output_folder, pref='denoise_'):
    img_path = Path(img_path)
    if not img_path.is_file():
        raise ValueError('{} does not exist'.format(img_path))
    if not Path(output_folder).is_dir():
        raise ValueError('{} does not exist'.format(output_folder))
    tmp_denoise = engine.run_denoise(str(img_path), str(output_folder), pref)['pth']['im'][0]
    if pref is not None or pref != '':
        output_denoise = Path(output_folder, pref + Path(tmp_denoise).name)
        shutil.copyfile(tmp_denoise, output_denoise)
        os.remove(tmp_denoise)
    else:
        output_denoise = tmp_denoise
    return output_denoise


def run_bb_spm(engine, img_path, output_folder, voxel_size):
    if not Path(img_path).is_file():
        raise ValueError('{} does not exist'.format(img_path))
    if not Path(output_folder).is_file():
        raise ValueError('{} does not exist'.format(output_folder))
    return engine.run_bb_spm(str(img_path), str(output_folder), voxel_size)['pth']['im'][0]


def matlab_check_module_path(engine, module_name):
    which = engine.which(module_name)
    if which:
        return str(Path(which).parent)
    print('{} was not found in matlab path'.format(module_name))
    path = input("You can either add the path to your startup.m (edit(fullfile(userpath,'startup.m')) in matlab or "
                 "you can enter the path to the module here. [n no or enter to skip/ quit or exit stop the "
                 "program]: ")
    if path.strip() in ['quit', 'q', 'exit']:
        print('Program stopped to fix matlab path issues')
        exit()
    if path.strip() not in ['', 'n', 'no']:
        if not Path(path).is_dir():
            raise ValueError('{} is not an existing directory'.format(path))
    else:
        return None
    return str(Path(path).absolute())


def images_avg(preproc_output_root, reg_type, method, output_pref, output_folder=None):
    if not Path(preproc_output_root).is_dir():
        raise ValueError('{} does not exist'.format(preproc_output_root))
    if not Path(output_folder).is_dir():
        raise ValueError('{} does not exist'.format(output_folder))
    final_dict = json.load(open(Path(preproc_output_root, '__final_preproc_dict.json')))
    bval_dict = {}
    for key in final_dict:
        for bval in final_dict[key]['denoise']:
            if bval in bval_dict:
                bval_dict[bval] += 1
            else:
                bval_dict[bval] = 1
    out_dict = {}
    for bval in bval_dict:
        img_list = []
        for key in final_dict:
            img_list.append(final_dict[key][reg_type][bval])

        engine = matlab.engine.start_matlab()
        matlab_scripts_folder = rsc.files('mri_preprocessing.matlab')
        engine.addpath(str(matlab_scripts_folder))
        output_path = engine.images_avg(img_list, method, output_folder, output_pref)
        out_dict[bval] = output_path
    return out_dict
