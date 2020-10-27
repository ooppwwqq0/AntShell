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
from antshell.utils.release import __prog__, __version__, __banner__
from antshell.utils.sqlite import Hosts
from antshell.utils.six import PY3
import os
import sys
if PY3:
    from functools import reduce


class BaseToolsBox(object):
    """base tools class"""

    def __init__(self, *args, **kwargs):
        self.rows, self.columns = os.popen("stty size", "r").read().split()
        self.base_path = os.getcwd()
        self.search = []
        self.vim_data = ''

    @staticmethod
    def getPath(paths, L=False):
        """Absolute path generation"""
        return reduce(lambda x,y:os.path.join(x,y), paths)

    @staticmethod
    def colorMsg(m="", c="red", flag=False, title=False, end='\n'):
        """Color text output"""
        sign = "30" if title else "1"
        colorCode = {
            "red": 31,
            "green": 32,
            "yellow": 33,
            "blue": 34,
            "pink": 35,
            "cblue": 36,
            "white": 37
        }
        color = colorCode.get(c, 31) + (10 if title else 0)
        colorSign = "\033[" + sign + ";" + str(color) + "m{0}\033[0m"
        msg = colorSign.format(m)
        if flag:
            return colorSign
        else:
            print(msg, end=end)
            return msg

    @staticmethod
    def isIp(ipaddr, c=False):
        """ip match
            ipaddr : ip
            c : Dan IP number, default False
        """

        if not ipaddr:
            return False
        q = ipaddr.strip().split('.')
        l = 4 if c else len(q)
        qi = map(int, filter(lambda x: x.isdigit(), q))
        return len(q) == l and len(
            list(filter(lambda x: x >= 0 and x <= 255, qi))) == l

    @staticmethod
    def getArgs(args="", fs=","):
        """Processing parameters
            args : parameters
        """
        return args.rsplit(fs) if args else False

    @staticmethod
    def __getSearch(searchList, match, search=""):
        if searchList:
            if match:
                search = """and ip in ({0}) """.format(",".join(
                    list(map(lambda x: "'%s'" % x, searchList))))
            else:
                search = """and ({0})""".format(" or ".join(
                    list(
                        map(lambda x: "name like '%%{0}%%' or ip like '%%{0}%%'".format(x),
                            searchList))))
        else:
            search = """and (name like '%%%%' or ip like '%%%%')"""
        return search

    def searchHost(self, include=None, pattern=False, match=False, search=""):
        '''
        获取主机信息, 基于sqlite3
        include : 用于过滤列表
        pattern : 开启返回空字典，默认False（不返回）
        match : 开启精确匹配模式，默认False（模糊匹配）
        '''

        if include:
            self.search.append(include)
        if search and search not in self.search:
            self.search.append(search)
        match = True if self.isIp(search, True) else match
        search = self.__getSearch(searchList=set(self.search), match=match)
        hosts = Hosts.select(w=search)
        if not hosts and not pattern:
            hosts = Hosts.select()
        self.Hlen = len(hosts)
        return hosts

    def __printInfo(self, key, k):
        user_name = k['sudo'] if k['sudo'] else k["user"]
        user_color = "yellow" if k['sudo'] else "green"
        bastion_color = "yellow" if int(k['bastion']) == 1 else "green"
        h = "{0} {1} {2}@{3}:{4} ".format(
            self.colorMsg(c="yellow", flag=True).format(
                "{0: >5}".format("[%s]" % str(key))),
            self.colorMsg(c=bastion_color, flag=True).format(
                "{0: <24}".format(k["name"][:24])),
            self.colorMsg(c=user_color, flag=True).format(
                "{0: >18}".format(user_name[:18])),
            self.colorMsg(c="green", flag=True).format(
                "{0: >15}".format(k["ip"][:15])),
            self.colorMsg(c="green", flag=True).format(
                "{0: <5}".format(k["port"])),
        )
        return h

    def printHosts(self, hosts="", cmode = None, limit=1, offset=15, pmax=0, flag=True):
        '''
        主机列表输出
        '''

        hosts = hosts if hosts else self.searchHost()
        count = 76
        maxm = int(int(self.columns) / count)
        Hlen = len(hosts)
        if not cmode:
            mode = maxm if maxm < 6 else 5
        else:
            mode = cmode if cmode <= maxm else maxm
        mode = Hlen if Hlen < mode else mode
        mode = mode if flag else 1

        limit = limit if limit else 1
        f = (limit-1) * offset + 1
        l = limit * offset + 1

        lines = '{0: >5} {1: <24} {2: >18}@{3: >15}:{4: <5} '
        msg = lines.format('[ID]', 'NAME', 'User', 'IP', 'PORT')
        tails = ' All Pages {0: <5} {1: <21}[c/C Clear] [n/N Back] Pages {2: <5}'
        tmsg = tails.format('[%s]' %pmax,'','[%s]'%limit)

        if not flag:
            os.system('clear')
        for i in range(mode):
            end = "\n" if i == mode - 1 else ""
            self.colorMsg(m=msg, c="white", title=True, end=end)
            if i < mode - 1:
                print("  |  ", end=end)

        for key in range(f, (Hlen + 1) if flag else (l if l<= self.Hlen else self.Hlen+1)):
            k = hosts[key - 1]
            h = self.__printInfo(key, k)
            if flag:
                rem = key % mode
                if mode == 1 or key == Hlen:
                    print(h)
                elif rem == 0:
                    print(h)
                elif rem < mode:
                    print(h, end='')
                    print("  |  ", end='')
            else:
                print(h)

        for i in range(mode):
            end = "\n" if i == mode - 1 else ""
            self.colorMsg(m=msg if flag else tmsg, c="cblue", title=True, end=end)
            if i < mode - 1:
                print("  |  ", end=end)


