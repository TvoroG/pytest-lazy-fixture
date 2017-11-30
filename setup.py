#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='pytest-lazy-fixture',
    version='0.4.0',
    author='Marsel Zaripov',
    author_email='marszaripov@gmail.com',
    maintainer='Marsel Zaripov',
    maintainer_email='marszaripov@gmail.com',
    license='MIT',
    url='https://github.com/tvorog/pytest-lazy-fixture',
    description='It helps to use fixtures in pytest.mark.parametrize',
    long_description=read('README.rst'),
    py_modules=['pytest_lazyfixture'],
    install_requires=['pytest>=2.9.2'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'pytest11': [
            'lazy-fixture = pytest_lazyfixture',
        ],
    },
)
