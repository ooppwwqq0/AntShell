#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/23 4:20 下午
# @Author  : Parsifal
# @File    : menu.py

import os
from sqlalchemy import or_

from antshell.models import SESSION, Hosts


class BaseMenu:

    def __init__(self):
        self.rows, self.columns = os.popen("stty size", "r").read().split()
        self.search = []
        self.Hlen = 0

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

    def set_search(self, search):
        if search and (search not in self.search):
            self.search.append(search)

    def clear_search(self):
        self.search = []

    def search_hosts(self, include=None, pattern=False, match=False, search=""):
        '''
        获取主机信息, 基于sqlite3
        include : 用于过滤列表
        pattern : 开启返回空字典，默认False（不返回）
        match : 开启精确匹配模式，默认False（模糊匹配）
        '''
        if include:
            self.set_search(include)
        self.set_search(search)
        match = True if self.isIp(search, True) else match
        if self.search:
            if match:
                hosts = SESSION.query(Hosts).filter(Hosts.ip.in_(list(map(lambda x: "%s" % x, self.search)))).all()
            else:
                hosts = SESSION.query(Hosts).filter(
                    or_(*list(map(lambda x: Hosts.ip.like('%%{0}%%'.format(x)), self.search)),
                        *list(map(lambda x: Hosts.name.like('%%{0}%%'.format(x)), self.search)))).all()
        else:
            hosts = SESSION.query(Hosts).all()

        if not hosts and not pattern:
            try:
                hosts = SESSION.query(Hosts).all()
            except Exception as e:
                return []
        self.Hlen = len(hosts)
        return hosts

    def title(self):
        pass

    def print(self, hosts=[], cmode=None, limit=1, offset=15, flag=True):
        """
        hosts：需要打印的主机列表
        cmode：多列模式中打印列数
        limit：当前打印页数
        offset：每页数据条数
        flag：是否多列显示（True（default）：多页显示并不刷新页面，False：单页显示并刷新页面）
        """
        pass

    def view(self, v, num, search, mode, default_page):
        pass
