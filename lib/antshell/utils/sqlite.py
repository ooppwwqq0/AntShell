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
from antshell.config import CONFIG
import os
import sys
import sqlite3


class getdb(object):
    '''
    初始化数据库
    '''

    def __init__(self, t="hosts"):
        self.t = t
        self.conn = self.__connect()
        self.db = self.conn.cursor()

    @staticmethod
    def __dict_factory(cursor, row):
        """turn data into a dictionary"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def __connect(self):
        """connect db"""
        dbPath = os.path.expanduser(CONFIG.DEFAULT.DB_PATH)
        if dbPath and os.path.isfile(dbPath):
            conn = sqlite3.connect(dbPath)
            conn.row_factory = self.__dict_factory
        return conn

    def select(self, w=None, **kwargs):
        sql = """select * from {0} where 1=1 {1} order by sort;"""
        if w:
            sql = sql.format(self.t, w)
        elif kwargs:
            f = "and {0} = '{1}'"
            wheres = [f.format(k, kwargs[k]) for k in kwargs]
            where = ' '.join(wheres)
            sql = sql.format(self.t, where)
        else:
            sql = sql.format(self.t, "")
        self.db.execute(sql)
        return [i for i in self.db]

    def insert(self, **kwargs):
        sql = """insert into {t}({rows}) values({vals});"""
        if kwargs:
            row = [key for key in kwargs]
            val = [str(kwargs[key]) for key in row]
            rows = ','.join(row)
            vals = '"' + '","'.join(val) + '"'
            sql = sql.format(t=self.t, rows=rows, vals=vals)
            self.db.execute(sql)
            self.conn.commit()
            return True
        else:
            return False

    def delete(self, rid):
        sql = """delete from {0} where id = {1};"""
        sql = sql.format(self.t, rid)
        self.db.execute(sql)
        return True

    def update(self):
        pass

    def __del__(self):
        self.conn.commit()
        self.conn.close()

DB = getdb
Hosts = getdb()