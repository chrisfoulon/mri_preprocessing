import json
from pathlib import Path


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


def check_output_integrity(output_folder):
    json_file = Path(output_folder, '__preproc_dict.json')
    if not json_file.is_file():
        return False

    json_dict = json.load(open(json_file, 'r'))
    if not json_dict:
        return False
    # There should always be only one key but it doesn't matter
    for key in json_dict:
        for output in json_dict[key]:
            for bval in json_dict[key][output]:
                for path in json_dict[key][output][bval]:
                    if not Path(path).is_file():
                        return False
    return True
