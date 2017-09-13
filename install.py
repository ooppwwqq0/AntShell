#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os, sys, time
import yaml
import sqlite3
reload(sys)
sys.setdefaultencoding('utf-8')

class BaseHandle(object):
    """暂时保留"""

    def __init__(self):
        """初始化"""
        C = GetConf()
        self.conf = C.conf(o=True)
        self.HOME = self.conf["HOME"]
        self.PWD = self.conf["PWD"]
        self.sshfile = self.getPath([self.conf["ODB_FILE"]])
        self.rows, self.columns = os.popen("stty size","r").read().split()
        self.ColorSign = self.colorMsg(flag=True).format("#")
        self.db = self._db()

    def _dict_factory(self,cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            if col[0] =="id":
                index = row[idx]
                continue
            d[col[0]] = row[idx]
        return (index, d)

    def _db(self):
        db_file = self.conf.get("DB_FILE")
        self.conn = conn = sqlite3.connect(db_file)
        conn.row_factory = self._dict_factory
        db = conn.cursor()
        return db

    def _commit(self):
        self.conn.commit()
        self.conn.close()

    def colorMsg(self, m="", c="red", flag=False):
        colorSign = {
            "red" : "\033[1;31m{0}\033[0m",
            "green" : "\033[1;32m{0}\033[0m",
            "yellow" : "\033[1;33m{0}\033[0m",
            "blue" : "\033[1;34m{0}\033[0m",
            "pink" : "\033[1;35m{0}\033[0m",
            "blue" : "\033[1;36m{0}\033[0m",
        }
        msg = colorSign.get(c).format(m)
        if flag:
            return colorSign.get(c)
        else:
            print(msg)
            return msg

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

    def getPath(self, args, L=False):
        """生成绝对路径"""

        path = "" if L else self.HOME
        for val in args:
            path = os.path.join(path, val)
        return path

    def isIp(self, ipaddr, c = False):
        """ip匹配
            ipaddr : 需要匹配的ip
            c : ip段数匹配，默认False
        """

        q = ipaddr.strip().split('.')
        l = 4 if c else len(q)
        qi = map(int, filter(lambda x: x.isdigit(), q))
        return len(q) == l and len(list(filter(lambda x: x >= 0 and x <= 255, qi))) == l

    def getArgs(self, args=""):
        """参数处理
            args : 原始参数
            sepa : 分隔符，默认","
        """
        sepa = option.fs if option.fs else ","
        cmds = args.rsplit(sepa) if args else False
        return cmds

def conf():
    f = open("./conf.yml")
    conf = yaml.load(f)
    return conf

def init_db():
    dbPath = c.get("DB_FILE")
    if dbPath:
        cmd = "sqlite3 %s '.read ./sql/init.sql'" %dbPath \
            if not os.path.isfile(dbPath) else False
        conn = sqlite3.connect(dbPath)
        db = conn.cursor()
        os.system(cmd) if cmd else ""

def get_old_info():
    sshfile = c.get("ODB_FILE")
    hosts = {}
    host_key= ['name', 'ip', 'user', 'passwd', 'port', 'sudo']
    key = 1
    with open(sshfile) as rhost:
        for line in rhost:
            lines = line.rstrip().rsplit('|')
            hosts[key] = dict(zip(host_key, lines))
            key += 1
    return hosts

def convert_to_db():
    db_file = c.get("DB_FILE")
    conn = sqlite3.connect(db_file)
    db = conn.cursor()
    h = get_old_info()
    for ki in h:
        k = h[ki]
        sql = """insert into hosts(name,ip,user,passwd,port,sudo)
            values('{0}','{1}','{2}','{3}',{4},{5})""".format(k["name"],k["ip"],k["user"],k["passwd"],k["port"],k["sudo"])
        db.execute(sql)
    conn.commit()
    conn.close()
    sys.exit()

def main():
    init_db()
    #convert_to_db()

if __name__ == "__main__":
    c = conf()
    main()
