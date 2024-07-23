#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='geometrychecking',
    packages=find_packages(),
    version='0.1.0',
    install_requires=[
        "numpy",
        "pandas",
        "click",
        "matplotlib",
        "pyarrow",
    ],
    #  entry_points={
        #  'console_scripts':[
            #  'extract-mapping = src.data.mapping:cli',
        #  ]
    #  }
)

