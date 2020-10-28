import json
from pathlib import Path


def get_dwi_lists_from_dict(split_dwi_dict):
    b0_list = [path for path in split_dwi_dict if split_dwi_dict[path] == 0.0]
    b1000_list = [path for path in split_dwi_dict if split_dwi_dict[path] != 0.0]
    return b0_list, b1000_list


def get_split_dict_from_json(json_path):
    json_path = Path(json_path)
    if not json_path.is_fifo():
        raise ValueError('{} does not exist'.format(json_path))
    json_dict = json.load(open(json_path, 'r'))
    split_dwi_dict = {key: json_dict[key]['split_dwi'] for key in json_dict if 'split_dwi' in json_dict[key]}
    return split_dwi_dict
