#!/usr/bin/env python
import os
from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='Tekton',
    version='0.1',
    description='Annotated Computer Network Graph',
    author='Ahmed El-Hassany',
    author_email='a.hassany@gmail.com',
    url='https://synet.etzh.ch',
    license = "Apache",
    packages=['tekton'],
    install_requires=[
        'ipaddress',
        'enum34',
        'future',
        'networkx>=2.2',
    ],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache License",
    ],
)
