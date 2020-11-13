import os
from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="mri_preprocessing",
    version="0.1",
    packages=find_packages(),
    scripts=[],
    zip_safe=True,
    include_package_data=True,
    # installed or upgraded on the target machine
    install_requires=["matlab",
                      "nibabel",
                      "numpy",
                      "scipy",
                      "pydicom"],

    package_data={
        # If any package contains *.txt or *.rst files, include them:
        "": ["*.txt", "*.rst"],
        # And include any *.m files found in the "matlab" directory, too:
        "matlab": ["*.m"],
        # Include all the executables from bin and data
        "bin": ["*"],
        "data": ["*"],
    },
    # https://reinout.vanrees.org/weblog/2010/01/06/zest-releaser-entry-points.html
    # entry_points could be used to automagically download dcm2niix depending on the OS of the user
    entry_points={
        'console_scripts': ['dwi_preproc = mri_preprocessing.scripts.dwi_preproc:main']
        # 'console_scripts': ['dicom_conversion = data_identification.scripts.dicom_conversion:convert']
    },

    # metadata to display on PyPI
    author="Chris Foulon",
    author_email="c.foulon@ucl.ac.uk",
    description="This project is about identifying the type of image and correcting headers during "
                "DICOM to nifti conversion",
    long_description=read('README.md'),
    keywords="DICOM nifti neuroimaging dwi",
    url="https://scm4.cs.ucl.ac.uk/Foukalas/data-identification-and-curation",   # project home page, if any
    project_urls={
        "Wiki": "https://scm4.cs.ucl.ac.uk/Foukalas/data-identification-and-curation/-/wikis/home",
    },
    classifiers=[
        "License :: OSI Approved :: Python Software Foundation License"
    ]
)
