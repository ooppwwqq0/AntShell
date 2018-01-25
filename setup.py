import os
import sys

sys.path.insert(0, os.path.abspath('lib'))
from antshell.release import __version__, __author__
try:
    from setuptools import setup, find_packages
    from setuptools.command.build_py import build_py as BuildPy
    from setuptools.command.install_lib import install_lib as InstallLib
    from setuptools.command.install_scripts import install_scripts as InstallScripts
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
    license='GPLv3+',
    install_requires=install_r,
    package_dir={ '': 'lib' },
    packages=find_packages('lib'),
    package_data={
        '': [
            'sql/*.sql',
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    scripts=[
        'bin/antshell',
        'bin/a'
    ],
    data_files=[],
)
