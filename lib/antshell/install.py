#!/usr/bin/env python
# -*- coding: utf-8 -*-

##########################################################################
# _______  __    _  _______  _______  __   __  _______  ___      ___     #
#|   _   ||  |  | ||       ||       ||  | |  ||       ||   |    |   |    #
#|  |_|  ||   |_| ||_     _||  _____||  |_|  ||    ___||   |    |   |    #
#|       ||       |  |   |  | |_____ |       ||   |___ |   |    |   |    #
#|       ||  _    |  |   |  |_____  ||       ||    ___||   |___ |   |___ #
#|   _   || | |   |  |   |   _____| ||   _   ||   |___ |       ||       |#
#|__| |__||_|  |__|  |___|  |_______||__| |__||_______||_______||_______|#
#                                                                        #
##########################################################################

from __future__ import (absolute_import, division, print_function)
from antshell.config import CONFIG, find_config_file
import os
import sys
import shutil


def init_db():
    '''
    初始化数据库
    '''

    dbPath = os.path.expanduser(CONFIG.DEFAULT.DB_PATH)
    if dbPath:
        db_dir = os.path.dirname(dbPath)
        if not os.path.isdir(db_dir):
            os.makedirs(db_dir)
        cwd = os.path.dirname(os.path.realpath(__file__))
        sql_path = os.path.join(cwd, "sql/init.sql")
        cmd = "sqlite3 %s '.read %s'" %(dbPath, sql_path) \
            if not os.path.isfile(dbPath) else False
        os.system(cmd) if cmd else ""


init_db()