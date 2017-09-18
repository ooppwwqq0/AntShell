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
from antshell.base import load_config
import os
import sys
import time
import yaml
import sqlite3
reload(sys)
sys.setdefaultencoding('utf-8')


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


def get_old_info(conf):
    sshfile = os.path.expanduser(conf.get("ODB_FILE"))
    hosts = {}
    host_key= ['name', 'ip', 'user', 'passwd', 'port', 'sudo']
    key = 1
    with open(sshfile) as rhost:
        for line in rhost:
            lines = line.rstrip().rsplit('|')
            hosts[key] = dict(zip(host_key, lines))
            key += 1
    return hosts


def convert_to_db(conf):
    dbPath = os.path.expanduser(conf.get("DB_FILE"))
    conn = sqlite3.connect(dbPath)
    db = conn.cursor()
    h = get_old_info(conf)
    for ki in h:
        k = h[ki]
        sql = """select * from hosts where name='{name}' and ip='{ip}'
            and user='{user}' and passwd='{passwd}' and port={port}
            and sudo={sudo};""".format(**k)
        db.execute(sql)
        has = [i for i in db]
        if len(has) == 0:
            sql = """insert into hosts(name,ip,user,passwd,port,sudo)
                values('{name}','{ip}','{user}','{passwd}',{port},{sudo})""".format(**k)
            db.execute(sql)
        else:
            print("already has record, skip")
    conn.commit()
    conn.close()
    sys.exit()

