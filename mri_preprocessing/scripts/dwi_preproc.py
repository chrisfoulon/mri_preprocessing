from pathlib import Path
import importlib_resources as rsc
import argparse
import json

from mri_preprocessing.modules import preproc, data_access, utils


def my_join(folder, file):
    return str(Path(folder, file))


def main():
    parser = argparse.ArgumentParser(description='Preprocess mri images')
    paths_group = parser.add_mutually_exclusive_group(required=True)
    paths_group.add_argument('-p', '--input_path', type=str, help='Root folder of the dataset')
    # paths_group.add_argument('-li-', '--input_list', type=str, help='Text file containing the list of DICOM folders'
    #                                                                 ' containing DWI images')
    paths_group.add_argument('-d', '--input_dict', type=str, help='File path to a __dict_save json or '
                                                                  '__final_image_dict.json type file')
    parser.add_argument('-o', '--output', type=str, help='output folder')
    parser.add_argument('-is', '--ignore_singletons', action='store_true', help='Turn off the research for matching '
                                                                                'images in case of singletons')
    parser.add_argument('-vs', '--voxel_size', type=float, default=2, help='output voxel size (default 2 for 2*2*2)')
    args = parser.parse_args()
    if args.input_path is not None:
        if not Path(args.input_path).is_dir():
            raise ValueError('{} is not an existing input directory'.format(args.input_path))
        json_path = Path(args.input_path, '__final_image_dict.json')
        if json_path.is_file():
            args.input_dict = json_path
        else:
            # Here we have a folder without the usual dicom_conversion output so we have to create a json and ignore
            # the matching of singletons
            json_dict = data_access.create_pseudo_input_dict(args.input_path)
            args.ignore_singletons = True
    if args.input_dict is not None:
        json_dict = Path(args.input_dict)
        if not json_dict.is_file():
            raise ValueError('{} is not an existing json'.format(json_dict))
        # json_dict = json.load(open(json_dict, 'r'))
    output_root = Path(args.output)
    if not output_root.is_dir():
        raise ValueError('{} is not an existing json'.format(output_root))
    if 'ignore_singletons' in args:
        pair_singletons = False
    else:
        pair_singletons = True
    output_preproc_dict = preproc.preproc_from_dataset_dict(json_dict, output_root,
                                                            rerun_strat='resume', output_vox_size=args.voxel_size,
                                                            pair_singletons=pair_singletons)
    utils.generate_final_preproc_dict(output_root)
    # output_json_file_path = Path(output_root, '__final_preproc_dict.json')
    # with open(output_json_file_path, 'w+') as out_file:
    #     json.dump(output_preproc_dict, out_file, indent=4)
    return
