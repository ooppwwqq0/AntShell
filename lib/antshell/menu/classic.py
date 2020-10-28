#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/27 11:09 上午
# @Author  : Parsifal
# @File    : classic.py

import math, os, sys

from antshell.config import CONFIG
from antshell.utils.release import __banner__
from antshell.menu.menu import BaseMenu


class ClassicMenu(BaseMenu):

    def title(self):
        os.system('clear')
        banner_color = CONFIG.DEFAULT.BANNER_COLOR
        self.colorMsg(__banner__.lstrip("\n"), banner_color)

    def __printInfo(self, index, k):
        user_name = k.sudo if k.sudo else k.user
        user_color = "yellow" if k.sudo else "green"
        bastion_color = "yellow" if int(k.bastion) == 1 else "green"
        h = "{0} {1} {2}@{3}:{4} ".format(
            self.colorMsg(c="yellow", flag=True).format(
                "{0: >5}".format("[%s]" % str(index))),
            self.colorMsg(c=bastion_color, flag=True).format(
                "{0: <24}".format(k.name[:24])),
            self.colorMsg(c=user_color, flag=True).format(
                "{0: >18}".format(user_name[:18])),
            self.colorMsg(c="green", flag=True).format(
                "{0: >15}".format(k.ip[:15])),
            self.colorMsg(c="green", flag=True).format(
                "{0: <5}".format(k.port)),
        )
        return h

    def print(self, hosts=[], cmode=None, limit=1, offset=15, flag=True):
        '''
        主机列表输出
        '''

        count = 76
        maxm = int(int(self.columns) / count)
        Hlen = len(hosts)
        pmax = int(math.ceil(Hlen / offset))
        if not cmode:
            mode = maxm if maxm < 6 else 5
        else:
            mode = cmode if cmode <= maxm else maxm
        mode = Hlen if Hlen < mode else mode
        mode = mode if flag else 1

        limit = limit if limit else 1
        limit = limit if limit <= pmax else pmax

        f = (limit - 1) * offset + 1
        l = limit * offset + 1

        lines = '{0: >5} {1: <24} {2: >18}@{3: >15}:{4: <5} '
        msg = lines.format('[ID]', 'NAME', 'User', 'IP', 'PORT')
        tails = ' All Pages {0: <5} {1: <21}[c/C Clear] [n/N Back] Pages {2: <5}'
        tmsg = tails.format('[%s]' % pmax, '', '[%s]' % limit)

        if not flag:
            self.title()
        for i in range(mode):
            end = "\n" if i == mode - 1 else ""
            self.colorMsg(m=msg, c="white", title=True, end=end)
            if i < mode - 1:
                print("  |  ", end=end)

        for index in range(f, (Hlen + 1) if flag else (l if l <= self.Hlen else self.Hlen + 1)):
            k = hosts[index - 1]
            h = self.__printInfo(index, k)
            if flag:
                rem = index % mode
                if mode == 1 or index == Hlen:
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

    def view(self, v, num, search, mode, default_page):
        '''
        用户交互形式选定主机
        '''
        print("asdasds")
        if v:
            try:
                num = int(v)
            except Exception:
                self.set_search(v)

        hosts = self.search_hosts(search=search)
        num = 1 if self.Hlen == 1 else num

        if not num:
            self.title()
            self.print(hosts=hosts, cmode=mode)
            limit, offset = 0, int(default_page if default_page != 0 else 15)
            pmax = int(math.ceil(self.Hlen / offset))

            while not num:
                try:
                    msg = """\nInput your choose or [ 'q' | ctrl-c ] to quit!\nServer [ ID | IP | NAME ] >> """
                    n = input(self.colorMsg(c="cblue", flag=True).format(msg))
                    if n in ('q', 'Q', 'quit', 'exit'):
                        sys.exit()
                    elif n in ('c', 'C', 'clear'):
                        self.clear_search()
                        hosts = self.search_hosts()
                    elif n in ('n', 'N'):
                        limit = (limit - 1) if limit > 1 else 1
                    elif n in ('m', 'M'):
                        limit = (limit + 1)
                    else:
                        try:
                            num = int(n) if int(n) <= self.Hlen else 0
                        except Exception:
                            if n:
                                self.set_search(n)
                                hosts = self.search_hosts(search=search)
                            else:
                                limit = (limit + 1)
                        num = 1 if self.Hlen == 1 else num
                    limit = limit if limit <= pmax else pmax
                except EOFError:
                    print("\r")
                except KeyboardInterrupt:
                    sys.exit("\r")
                self.print(hosts=hosts, limit=limit, offset=offset, flag=False)
        return hosts[num - 1]


Classic = ClassicMenu()
