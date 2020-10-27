#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/22 9:18 下午
# @Author  : Parsifal
# @File    : __init__.py

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import os
from antshell.config import CONFIG
from sqlalchemy import create_engine

dbPath = os.path.expanduser(CONFIG.DEFAULT.DB_PATH)
engine = create_engine('sqlite:///' + dbPath + '?check_same_thread=False', echo=False)
from sqlalchemy.orm import sessionmaker

# engine是2.2中创建的连接
Session = sessionmaker(bind=engine,)

# 创建Session类实例
SESSION = Session()