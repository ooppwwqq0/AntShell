#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/27 11:09 上午
# @Author  : Parsifal
# @File    : classic.py

import math
import os
from antshell.config import CONFIG
from antshell.utils.release import __banner__
from menu.menu import BaseMenu

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
        limit = limit if limit <= pmax else pmax
        if not cmode:
            mode = maxm if maxm < 6 else 5
        else:
            mode = cmode if cmode <= maxm else maxm
        mode = Hlen if Hlen < mode else mode
        mode = mode if flag else 1

        limit = limit if limit else 1
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


Classic = ClassicMenu()
