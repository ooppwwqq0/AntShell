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
from antshell.utils.errors import AntShellError
import os
import sys
import sqlite3


class Sqlite(object):
    '''
    初始化数据库
    '''

    def __init__(self, t="hosts"):
        self.t = t
        try:
            self.conn = self.__connect()
            self.db = self.conn.cursor()
        except Exception:
            raise AntShellError("Can Not Find DB File!")

    @staticmethod
    def __dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def __connect(self):
        conn = None
        dbPath = os.path.expanduser(CONFIG.DEFAULT.DB_PATH)
        if dbPath and os.path.isfile(dbPath):
            conn = sqlite3.connect(dbPath)
            conn.row_factory = self.__dict_factory
        return conn

    def select(self, w=None, **kwargs):
        sql = """select * from {t} where 1=1 {w} order by sort;"""
        if w:
            sql = sql.format(t=self.t, w=w)
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
        try:
            if kwargs:
                row = [key for key in kwargs]
                val = [str(kwargs[key]) for key in row]
                rows = ','.join(row)
                vals = '"' + '","'.join(val) + '"'
                sql = sql.format(t=self.t, rows=rows, vals=vals)
                self.db.execute(sql)
                self.conn.commit()
                return True
        except Exception:
            return False

    def delete(self, pk):
        sql = """delete from {t} where id = {pk};"""
        try:
            sql = sql.format(t=self.t, pk=pk)
            self.db.execute(sql)
            self.conn.commit()
            return True
        except Exception:
            return False

    def update(self, pk, hosts):
        sql = """update {t} set {rows} where id={pk};"""
        f = "{0}='{1}'"
        try:
            keyList = [f.format(k, hosts[k]) for k in hosts]
            sql = sql.format(t=self.t, rows=','.join(keyList), pk=pk)
            self.db.execute(sql)
            self.conn.commit()
            return True
        except Exception:
            return False

    def __del__(self):
        try:
            self.conn.commit()
            self.conn.close()
        except Exception:
            raise AntShellError("Can Not Find DB File!")

DB = Sqlite
Hosts = DB(t="hosts")