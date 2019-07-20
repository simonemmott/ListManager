import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='k2_util',
    version='0.0.2',
    author_email='simon.emmott@yahoo.co.uk',
    author='Simon Emmott',
    description='Utilities developed for K2 application servers',
    packages=['k2_util', 'tests'],
    long_description=read('README.md'),
    install_requires=[
        'python-string-utils'
    ],
)