import os
import sys

sys.path.insert(0, os.path.abspath('lib'))
from antshell.release import __version__, __author__
try:
    from setuptools import setup, find_packages
except ImportError:
    print('not found setuptools')
    sys.exit(1)

with open('requirements.txt') as r_file:
    install_r = r_file.read().splitlines()
    if not install_r:
        print('Unable to read requirements from the requirements.txt file')
        sys.exit(2)

setup(
    name='antshell',
    version=__version__,
    description='AntShell Auto SSH',
    author=__author__,
    author_email='emo_ooppwwqq0@163.com',
    url='http://c.isme.pub/AntShell',
    license='GPLv3',
    install_requires=install_r,
    package_dir={ '': 'lib' },
    packages=find_packages('lib'),
    package_data={
        '': []
    },
    classifiers=[],
    scripts=[
        'bin/antshell',
        'bin/a'
    ],
    data_files=[],
)
