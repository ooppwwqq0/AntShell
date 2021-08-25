#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/22 9:18 下午
# @Author  : Parsifal
# @File    : __init__.py

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from antshell.config import CONFIG
except:
    pass
from antshell.models.Hosts import Hosts
from antshell.models.Groups import Groups


dbPath = os.path.expanduser(CONFIG.DEFAULT.DB_PATH)
if dbPath:
    db_dir = os.path.dirname(dbPath)
    if not os.path.isdir(db_dir):
        os.makedirs(db_dir)
engine = create_engine('sqlite:///' + dbPath + '?check_same_thread=False', echo=False)

# engine是2.2中创建的连接
Session = sessionmaker(bind=engine, )

# 创建Session类实例
SESSION = Session()

Hosts.__table__.create(engine, checkfirst=True)
Groups.__table__.create(engine, checkfirst=True)
