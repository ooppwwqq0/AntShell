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
from antshell.base import find_config_file, load_config
from antshell.dbtools import getdb
import os
import sys
import shutil
import time
import yaml
import sqlite3


class BaseHandle(object):
    """暂时保留"""

    def oldGetHost(self, include = None, pattern = False, match = False):
        """获取主机信息,old数据
            include : 用于过滤列表
            pattern : 开启返回空字典，默认False（不返回）
            match : 开启精确匹配模式，默认False（模糊匹配）
        """

        include = option.search if option.search else include
        if include:
            match = True if self.isIp(include, True) else match
        ahost, nhost = {}, {}
        host_key= ['name', 'ip', 'user', 'passwd', 'port', 'sudo']
        key, ikey = 1, 1
        includes = self.getArgs(include)
        with open(self.sshfile) as rhost:
            for line in rhost:
                lines = line.rstrip().rsplit('|')
                ahost[key] = dict(zip(host_key, lines))
                key += 1
        if includes:
            if match:
                res = list(filter(lambda x:ahost[x]["ip"] in includes, ahost))
            else:
                def filterNomatch(k):
                    f = list(filter(lambda x:x in ahost[k]["name"] or x in ahost[k]["ip"], includes))
                    return k if f else False
                res = list(filter(filterNomatch, ahost))
            for i in res:
                nhost[ikey] = ahost[i]
                ikey += 1
        if len(nhost) != 0 or pattern:
            return nhost
        return ahost

    def searchHost(self, include = None, pattern = False, match = False):
        """获取主机信息, 基于sqlite3
            include : 用于过滤列表
            pattern : 开启返回空字典，默认False（不返回）
            match : 开启精确匹配模式，默认False（模糊匹配）
        """

        include = option.search if option.search else include
        if include:
            match = True if self.isIp(include, True) else match
        includes = self.getArgs(include)
        ahost, nhost = {}, {}
        sql = """select id,name,ip,user,passwd,port,sudo
            from hosts where 1=1 {0} order by sort;"""
        self.db.execute(sql.format(""))
        for k in self.db:
            ahost[k[0]] = k[1]
        if includes:
            if match:
                res = list(filter(lambda x:ahost[x]["ip"] in includes, ahost))
            else:
                def filterNomatch(k):
                    f = list(filter(lambda x:x in ahost[k]["name"] or x in ahost[k]["ip"], includes))
                    return k if f else False
                res = list(filter(filterNomatch, ahost))
            for i in res:
                nhost[ikey] = ahost[i]
                ikey += 1
        if len(nhost) != 0 or pattern:
            return nhost
        return ahost


def init_db(conf):
    dbPath = os.path.expanduser(conf.get("DB_FILE"))
    if dbPath:
        cwd = os.path.dirname(os.path.realpath(__file__))
        sql_path = os.path.join(cwd, "sql/init.sql")
        cmd = "sqlite3 %s '.read %s'" %(dbPath, sql_path) \
            if not os.path.isfile(dbPath) else False
        os.system(cmd) if cmd else ""


def init_conf():
    path = find_config_file()
    if not path:
        default_path= "~/.antshell"
        if not os.path.exists(default_path):
            dpath = os.path.expanduser(default_path)
            os.makedirs(dpath)
        config_name = "antshell.yml"
        cwd = os.path.dirname(os.path.realpath(__file__))
        shutil.copy(os.path.join(cwd, "config/", config_name), os.path.join(dpath, config_name))


def get_old_info(conf):
    sshfile = os.path.expanduser(conf.get("ODB_FILE"))
    hosts = {}
    host_key= ['name', 'ip', 'user', 'passwd', 'port', 'sudo']
    key = 1
    if os.path.exists(sshfile) and os.path.isfile(sshfile):
        with open(sshfile) as rhost:
            for line in rhost:
                lines = line.rstrip().rsplit('|')
                hosts[key] = dict(zip(host_key, lines))
                key += 1
    else:
        lines = ["test", "127.0.0.1", "root", "", 22, 1]
        hosts[key] = dict(zip(host_key, lines))
    return hosts


def file_convert_to_db():
    db = getdb(conf)
    h = get_old_info(conf)
    for k in h:
        res = db.select(**h[k])
        has = [x for x in res]
        if len(has) == 0:
            db.insert(**h[k])
        else:
            print("already has record, skip")


def db_convert_to_file(conf):
    db = getdb(conf)
    res = db.select()
    for i in res:
        print(i)


def main():
    global conf
    conf = load_config()
    #file_convert_to_db()
    db_convert_to_file()


if __name__ == "__main__":
    main()
