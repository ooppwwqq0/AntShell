#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/23 4:20 下午
# @Author  : Parsifal
# @File    : menu.py

import os



class BaseMenu:

    def __init__(self):
        self.rows, self.columns = os.popen("stty size", "r").read().split()
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

