import shutil
from pathlib import Path
import os

""" Matlab modules management: store the path to the local matlab modules somewhere in the package install. 
The first time the scripts are used, check if the matlab paths have been setup, if not, ask if you want to set them up.
"""

# pp_module_path = '/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/Patient-Preprocessing/'
# sr_module_path = '/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/spm_superres/'


def my_join(folder, file):
    return str(Path(folder, file))


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
