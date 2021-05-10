from pathlib import Path
import json


def generate_final_preproc_dict(output_dir, final_dict_path=''):
    final_preproc_dict = {}
    if final_dict_path == '':
        final_preproc_dict_path = Path(output_dir, '__final_preproc_dict.json')
    else:
        final_preproc_dict_path = final_dict_path
    for d in Path(output_dir).iterdir():
        preproc_json = Path(d, '__preproc_dict.json')
        if preproc_json.is_file():
            final_preproc_dict.update(json.load(open(preproc_json, 'r')))
    with open(final_preproc_dict_path, 'w+') as out_file:
        json.dump(final_preproc_dict, out_file, indent=4)
    return final_preproc_dict
