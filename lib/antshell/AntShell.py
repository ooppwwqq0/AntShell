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
from antshell.config import CONFIG
from antshell.install import init_db
from antshell.paramikos import ParaTools
from antshell.utils.parser import load_argParser
from antshell.utils.errors import DeBug
from antshell.utils.sqlite import Hosts
from antshell.utils.ssh import SShTools
from antshell.utils.release import __banner__
from antshell.utils.six import PY2

import math
import os
import sys
import time

if PY2:
    input = raw_input
    reload(sys)
    sys.setdefaultencoding('utf-8')

DEBUG = CONFIG.DEFAULT.DEBUG


class HostHandle(SShTools, ParaTools):
    """主机交互连接处理"""

    def __init__(self):
        super(HostHandle, self).__init__()
        self.HOME = os.environ["HOME"]
        self.hinfo = []
        self.Hlen = 0
        self.hosts = Hosts

    @staticmethod
    def __getInfo(ip):
        """获取用户相关信息"""
        info = {
            "name": option.name if option.name else ip,
            "ip": ip,
            "user": option.user if option.user else CONFIG.USER.USERNAME,
            "passwd": option.passwd if option.passwd else CONFIG.USER.PASSWORD,
            "port": option.port if option.port else CONFIG.USER.PORT,
            "sudo": option.sudo,
            "bastion": 1 if option.bastion else 0
        }

        return info

    def __editList(self, ip):
        """主机信息"""
        ipt = self.isIp(ip, True)
        if ipt:
            res = self.searchHost(include=ip, pattern=True, match=True, search=option.search)
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
            self.hosts.insert(**info)
        else:
            print(res)
            sys.exit()

    def delList(self):
        """删除主机信息"""
        res, info = self.__editList(option.dels)
        if len(res) > 0:
            print(info)
            task = [self.hosts.delete(rid = x["id"]) for x in res]
            self.colorMsg("del ip %s success !" % option.dels, "blue")
        elif len(res) == 0:
            self.colorMsg("ip %s not exist !" % option.dels)
        sys.exit()

    def connect(self):
        """用户交互形式选定主机"""

        if option.v:
            try:
                option.num = int(option.v)
            except Exception:
                self.search.append(option.v)
        hosts = self.searchHost(search=option.search)
        option.num = 1 if self.Hlen == 1 else option.num
        if not option.num:
            os.system('clear')
            banner_color = CONFIG.DEFAULT.BANNER_COLOR
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
                        hosts = self.searchHost(search=option.search)
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
                                hosts = self.searchHost(search=option.search)
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
        hosts = self.searchHost(search=option.search)[option.num - 1]
        banner_color = CONFIG.DEFAULT.BANNER_COLOR
        self.colorMsg(__banner__.lstrip("\n"), banner_color)
        DeBug(hosts, DEBUG)
        self.get_connect(hosts, agent=option.agent, sudo=option.sudo)


def main():
    """主函数"""

    global option

    parser = load_argParser()
    option = parser.parse_args()

    try:
        if option.init:
            init_db()
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
