from pathlib import Path
import typing

import numpy as np
from scipy.spatial.distance import euclidean
from scipy.ndimage.measurements import center_of_mass
from bcblib.tools.nifti_utils import load_nifti


def get_centre_of_mass(nifti, round_coord=False):
    nii = load_nifti(nifti)
    if round_coord:
        return np.round(center_of_mass(nii.get_fdata()))
    else:
        return center_of_mass(nii.get_fdata())


def centre_of_mass_difference(nifti, reference, round_centres=False):
    if not isinstance(reference, typing.Sequence):
        reference = get_centre_of_mass(reference, round_centres)
    nii_centre = get_centre_of_mass(nifti, round_centres)
    if len(nii_centre.shape) != len(reference.shape):
        raise ValueError('Nifti image and reference must have the same number of dimensions')
    return euclidean(nii_centre, reference)


def centre_of_mass_difference_list(nifti_list, reference, fname_filter=None, round_centres=False):
    if fname_filter is not None:
        nifti_list = [f for f in nifti_list if fname_filter in Path(f).name]
    distance_dict = {}
    for f in nifti_list:
        distance_dict[str(f)] = centre_of_mass_difference(f, reference, round_centres)
    return distance_dict
