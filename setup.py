from __future__ import print_function

import json
import os
import os.path
import re
import sys
import warnings

from collections import defaultdict
from distutils.command.build_scripts import build_scripts as BuildScripts
from distutils.command.sdist import sdist as SDist

try:
    from setuptools import setup, find_packages
    from setuptools.command.build_py import build_py as BuildPy
    from setuptools.command.install_lib import install_lib as InstallLib
    from setuptools.command.install_scripts import install_scripts as InstallScripts
except ImportError:
    print('not found setuptools')
    sys.exit(1)

sys.path.insert(0, os.path.abspath('lib'))
from antshell.utils.release import __version__, __author__

PYCRYPTO_DIST = 'pycrypto'

def read_file(file_name):
    """Read file and return its contents."""
    with open(file_name, 'r') as f:
        return f.read()

def read_requirements(file_name):
    """Read requirements file as a list."""
    reqs = read_file(file_name).splitlines()
    if not reqs:
        raise RuntimeError(
            "Unable to read requirements from the %s file"
            "That indicates this copy of the source code is incomplete."
            % file_name
        )
    return reqs

def read_extras():
    """Specify any extra requirements for installation."""
    extras = dict()
    extra_requirements_dir = 'packaging/requirements'
    for extra_requirements_filename in os.listdir(extra_requirements_dir):
        filename_match = re.search(r'^requirements-(\w*).txt$', extra_requirements_filename)
        if not filename_match:
            continue
        extra_req_file_path = os.path.join(extra_requirements_dir, extra_requirements_filename)
        try:
            extras[filename_match.group(1)] = read_file(extra_req_file_path).splitlines()
        except RuntimeError:
            pass
    return extras

def get_crypto_req():
    """Detect custom crypto from ANSIBLE_CRYPTO_BACKEND env var.

    pycrypto or cryptography. We choose a default but allow the user to
    override it. This translates into pip install of the sdist deciding what
    package to install and also the runtime dependencies that pkg_resources
    knows about.
    """
    crypto_backend = os.environ.get('ANSIBLE_CRYPTO_BACKEND', '').strip()

    if crypto_backend == PYCRYPTO_DIST:
        # Attempt to set version requirements
        return '%s >= 2.6' % PYCRYPTO_DIST

    return crypto_backend or None

def substitute_crypto_to_req(req):
    """Replace crypto requirements if customized."""
    crypto_backend = get_crypto_req()

    if crypto_backend is None:
        return req

    def is_not_crypto(r):
        CRYPTO_LIBS = PYCRYPTO_DIST, 'cryptography'
        return not any(r.lower().startswith(c) for c in CRYPTO_LIBS)

    return [r for r in req if is_not_crypto(r)] + [crypto_backend]

def get_dynamic_setup_params():
    """Add dynamically calculated setup params to static ones."""
    return {
        # Retrieve the long description from the README
        # 'long_description': read_file('README.rst'),
        'install_requires': substitute_crypto_to_req(
            read_requirements('requirements.txt'),
        ),
        # 'extras_require': read_extras(),
    }

static_setup_params = dict(
    # Use the distutils SDist so that symlinks are not expanded
    # Use a custom Build for the same reason
    cmdclass={},
    name='antshell',
    version=__version__,
    description='AntShell Auto SSH',
    author=__author__,
    author_email='emo_ooppwwqq0@163.com',
    url='https://c.isme.pub/AntShell',

    project_urls={
        'Source Code': 'https://github.com/ooppwwqq0/AntShell',
    },
    license='GPLv3+',
    # Ansible will also make use of a system copy of python-six and
    # python-selectors2 if installed but use a Bundled copy if it's not.

    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
    package_dir={'': 'lib'},
    packages=find_packages('lib'),
    package_data={
        '': [
            'sql/*.sql',
            'config/antshell.yml',
            'config/antshell.cfg',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    scripts=[
        'bin/antshell',
        'bin/a'
    ],
    data_files=[],
    # Installing as zip files would break due to references to __file__
    zip_safe=False
)

def main():
    """Invoke installation process using setuptools."""
    setup_params = dict(static_setup_params, **get_dynamic_setup_params())
    ignore_warning_regex = (
        r"Unknown distribution option: '(project_urls|python_requires)'"
    )
    warnings.filterwarnings(
        'ignore',
        message=ignore_warning_regex,
        category=UserWarning,
        module='distutils.dist',
    )
    setup(**setup_params)
    warnings.resetwarnings()

if __name__ == '__main__':
    main()
