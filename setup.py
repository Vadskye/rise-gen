#!/usr/bin/env python3

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages
import os

content_data_files = list()
for dir_path, dir_names, file_names in os.walk('content'):
    # for now, ignore subdirectories
    content_data_files += [os.path.join('content', file_name)
                           for file_name in file_names]

config = {
    'description': 'Generation tools for Rise',
    'author': 'vadskye',
    'version': '0.1',
    'name': 'rise_gen',
    'packages': find_packages(),
    'package_data': {
        'rise_gen': ['content/*.yaml'],
    },
    'include_package_data': True,
    'zip_safe': False,
    'data_files': [('content', content_data_files)],
}

setup(**config)
