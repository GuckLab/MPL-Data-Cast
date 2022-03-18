from os.path import dirname, realpath, exists
from setuptools import setup, find_packages
import sys


maintainer = u"Paul Müller"
maintainer_email = "dev@craban.de"
description = 'Convert and transfer data to network shares at MPL'
name = 'mpl_data_cast'
year = "2022"

sys.path.insert(0, realpath(dirname(__file__))+"/"+name)
from _version import version  # noqa: E402

setup(
    name=name,
    maintainer=maintainer,
    maintainer_email=maintainer_email,
    url='https://github.com/GuckLab/MPL-Data-Cast',
    version=version,
    packages=find_packages(),
    package_dir={name: name},
    include_package_data=True,
    license="GPL v3",
    description=description,
    long_description=open('README.rst').read() if exists('README.rst') else '',
    install_requires=[
        "click>=8",
        "dclab>=0.39.15",
        "h5py>=2.8.0",
        "numpy>=1.21",  # CVE-2021-33430
        "pyqt6",
    ],
    python_requires='>=3.9, <4',
    entry_points={
        "gui_scripts": ['mpl_data_cast = mpl_data_cast.__main__:main'],
        "console_scripts": ["mpldc = mpl_data_cast.cli:cli"]},
    keywords=["Data maintenance", "MPL", "Max Planck"],
    classifiers=['Operating System :: OS Independent',
                 'Programming Language :: Python :: 3',
                 'Intended Audience :: Science/Research',
                 ],
    platforms=['ALL']
    )
