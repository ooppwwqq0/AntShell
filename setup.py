#!/usr/bin/env python
# -*- coding: utf-8 -*-

# setup.py
#from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name="antshell",
    version="0.4",
    author="Casstiel",
    author_email="emo_ooppwwqq0@163.com",
    maintainer_email="emo_ooppwwqq0@163.com",
    description="AntShell Auto SSH",
    url="http://c.isme.pub/AntShell",
    packages= find_packages(),
    install_requires=[
        "paramiko>=2.1.1",
    ]
)
