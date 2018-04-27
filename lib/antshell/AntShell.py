#!/usr/bin/env python
# -*- coding:utf-8 -*-

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
from antshell.base import BaseToolsBox, __banner__
from antshell.base import load_config, load_argParser
from antshell.install import init_db, init_conf, file_convert_to_db
from antshell.paramikos import ParaTools
from antshell.dbtools import getdb
from antshell.ssh import SShTools
import math
import os
import sys
import time

if sys.version < '3':
    input = raw_input
    reload(sys)
    sys.setdefaultencoding('utf-8')


class HostHandle(BaseToolsBox, SShTools, ParaTools):
    """主机交互连接处理"""

    def __init__(self):
        super(HostHandle,self).__init__()
        self.HOME = os.environ["HOME"]
        self.rows, self.columns = os.popen("stty size", "r").read().split()
        self.base_path = os.getcwd()
        self.hinfo = []
        self.Hlen = 0
        self.search = []
        self.db = getdb(conf)
        self.key_path = os.path.expanduser(conf.get("KEY_PATH"))

    def searchHost(self, include=None, pattern=False, match=False):
        """获取主机信息, 基于sqlite3
            include : 用于过滤列表
            pattern : 开启返回空字典，默认False（不返回）
            match : 开启精确匹配模式，默认False（模糊匹配）
        """

        if include:
            self.search.append(include)
        if option.search not in self.search:
            self.search.append(option.search)
        match = True if self.isIp(option.search, True) else match
        search = self.__getSearch(set(self.search), match)
        hosts = self.db.select(w=search)
        if not hosts and not pattern:
            hosts = self.db.select()
        self.Hlen = len(hosts)
        return hosts

    @staticmethod
    def __getSearch(includes, match, search=""):
        if includes:
            if match:
                search = """and ip in ({0}) """.format(",".join(
                    list(map(lambda x: "'%s'" % x, includes))))
            else:
                search = """and ({0})""".format(" or ".join(
                    list(
                        map(lambda x: "name like '%%{0}%%' or ip like '%%{0}%%'".format(x),
                            includes))))
        return search

    @staticmethod
    def __getInfo(ip):
        """获取用户相关信息"""
        info = {
            "name": option.name if option.name else ip,
            "ip": ip,
            "user": option.user if option.user else conf.get("USER"),
            "passwd": option.passwd if option.passwd else conf.get("PASS"),
            "port": option.port if option.port else conf.get("PORT"),
        }
        info["sudo"] = 0 if info["user"] == "root" else 1
        return info

    def __editList(self, ip):
        """主机信息"""
        ipt = self.isIp(ip, True)
        if ipt:
            res = self.searchHost(ip,True,True)
            info = self.__getInfo(ip)
            res = list(filter(
                lambda x:x["user"] == info.get("user") \
                and x["port"] == info.get("port"), res
            ))
            self.search.append(ip)
            return res, info
        else:
            self.colorMsg("wrong ip !")
            sys.exit()

    def addList(self):
        """添加主机信息"""
        res, info = self.__editList(option.add)
        if len(res) == 1:
            self.colorMsg("already exist !")
        elif len(res) == 0:
            self.db.insert(**info)
        else:
            print(res)
            sys.exit()

    def delList(self):
        """删除主机信息"""
        res, info = self.__editList(option.dels)
        if len(res) > 0:
            print(info)
            task = [self.db.delete(rid = x["id"]) for x in res]
            self.colorMsg("del ip %s success !" % option.dels, "blue")
        elif len(res) == 0:
            self.colorMsg("ip %s not exist !" % option.dels)
        sys.exit()

    def connect(self):
        """用户交互形式选定主机"""

        if option.v:
            try:
                option.num = int(option.v)
            except Exception as e:
                self.search.append(option.v)
        hosts = self.searchHost()
        option.num = 1 if self.Hlen == 1 else option.num
        if not option.num:
            clear = os.system('clear')
            banner_color = conf.get("banner_color")
            self.colorMsg(__banner__.lstrip("\n"), banner_color)
            self.printHosts(hosts = hosts, cmode=option.mode)
            limit, offset = 0, 15
            while not option.num:
                try:
                    msg = """\ninput num or [ 'q' | ctrl-c ] to quit!\nServer Id >> """
                    n = input(
                        self.colorMsg(c="cblue", flag=True).format(msg))
                    if n in ('q', 'Q', 'quit', 'exit'):
                        sys.exit()
                    elif n in ('c', 'C', 'clear'):
                        option.search = None
                        self.search = []
                        hosts = self.searchHost()
                    elif n in ('n','N'):
                        limit = (limit - 1) if limit > 1 else 1
                    elif n in ('m','M'):
                        limit = (limit + 1)
                    else:
                        try:
                            option.num = int(n) if int(n) <= self.Hlen else 0
                        except Exception as e:
                            if n:
                                self.search.append(n)
                                hosts = self.searchHost()
                            else:
                                limit = (limit + 1)
                        option.num = 1 if self.Hlen == 1 else option.num
                    if option.num:
                        break
                except EOFError as e:
                    print("\r")
                except KeyboardInterrupt as e:
                    sys.exit("\r")
                pmax = int(math.ceil(self.Hlen/offset))
                limit = limit if limit <= pmax else pmax
                self.printHosts(hosts=hosts, limit=limit, offset=offset, pmax=pmax, flag=False)
        hosts = self.searchHost()[option.num - 1]
        banner_color = conf.get("banner_color")
        self.colorMsg(__banner__.lstrip("\n"), banner_color)
        print(hosts)
        self.get_connect(hosts, agent=option.agent)


def main():
    """主函数"""

    global conf
    global option

    conf = load_config()
    if not conf:
        print("load config error")
        sys.exit()

    parser = load_argParser()
    option = parser.parse_args()

    try:
        if option.init:
            init_db(conf)
            init_conf()
            sys.exit()
        elif option.update:
            init_db(conf)
            file_convert_to_db(conf)
            sys.exit()

        h = HostHandle()
        if option.lists:
            h.printHosts()
            sys.exit()
        elif option.dels:
            h.delList()
        elif option.add:
            h.addList()
        elif option.para or option.get or option.put:
            h.mygevent(option)

        #clear = os.system('clear')
        h.connect()
    except Exception as e:
        print(e)
        # print(parser.print_help())
    finally:
        sys.exit()


if __name__ == "__main__":
    main()
