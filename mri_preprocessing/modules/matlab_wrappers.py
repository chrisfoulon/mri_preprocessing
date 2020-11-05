from pathlib import Path
import shutil
import os


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
