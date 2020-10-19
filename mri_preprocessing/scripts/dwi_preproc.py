import os
import sys
import shutil
from pathlib import Path


import matlab.engine
eng = matlab.engine.start_matlab()
eng.addpath('/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/dwi_preproc_module')
eng.addpath('/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/Patient-Preprocessing/')
eng.addpath('/home/tolhsadum/neuro_apps/MATLAB/HighDimNeuro/spm_superres/')


def my_join(folder, file):
    return str(Path(folder, file))


input_file = Path(sys.argv[1])
input_basename = input_file.name
denoise_basename = 'denoise_' + input_basename
nonlinear_basename = 'nonlinear_' + input_basename
# Everything has to be a string otherwise matlab explodes because it's the best language ever
output_folder = str(Path(sys.argv[2]))
if not Path.is_dir(Path(sys.argv[2])):
    os.makedirs(output_folder)
tmp_folder = str(Path(output_folder, 'tmp'))
if not os.path.isdir(tmp_folder):
    os.makedirs(tmp_folder)
# preproc_image_path = os.path.join(output_folder, os.path.basename(input_file))
tmp_image_path = str(Path(tmp_folder, input_basename))
shutil.copyfile(str(input_file), tmp_image_path)

print('######################')
print('RESET ORIGIN')
print('######################')
eng.reset_orient_mat(str(tmp_image_path), nargout=0)
tmp_denoise = my_join(tmp_folder, denoise_basename)
output_nonlinear = my_join(output_folder, nonlinear_basename)
shutil.copyfile(tmp_image_path, tmp_denoise)
eng.run_denoise(tmp_denoise, output_folder)
# Will be created by run_denoise (RunPreproc call)
out_denoise = my_join(output_folder, denoise_basename)
out_align = eng.my_align(out_denoise, tmp_folder)
tmp_rigid = out_align['rigid']
tmp_affine = out_align['affine']
eng.run_bb_spm(tmp_rigid, output_folder, 2)
eng.run_bb_spm(tmp_affine, output_folder, 2)

shutil.copyfile(tmp_rigid, output_nonlinear)
eng.non_linear_reg(output_nonlinear)
"""
OUTPUT1: denoise_
OUTPUT2: rigid_
OUTPUT3: affine_
OUTPUT4: nonlinear_
1) Reset origin in tmp
2) Denoise in tmp copy to out/OUTPUT1 + tmp/OUTPUT2 + tmp/OUTPUT3 + tmp/OUTPUT4 
3) Affine align tmp/OUTPUT3
4) Apply transform to out/OUTPUT3 with bb_spm
5) Rigid align OUTPUT4 copy
6) Apply transform to out/OUTPUT2 with bb_spm
7) compute and apply non-linear transform to out/OUTPUT4
"""