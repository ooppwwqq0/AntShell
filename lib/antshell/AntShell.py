#!/usr/bin/env python
# -*- coding:utf-8 -*-

##########################################################################
# _______  __    _  _______  _______  __   __  _______  ___      ___     #
# |   _   ||  |  | ||       ||       ||  | |  ||       ||   |    |   |    #
# |   _   ||  |  | ||       ||       ||  | |  ||       ||   |    |   |    #
# |  |_|  ||   |_| ||_     _||  _____||  |_|  ||    ___||   |    |   |    #
# |       ||       |  |   |  | |_____ |       ||   |___ |   |    |   |    #
# |       ||  _    |  |   |  |_____  ||       ||    ___||   |___ |   |___ #
# |   _   || | |   |  |   |   _____| ||   _   ||   |___ |       ||       |#
# |__| |__||_|  |__|  |___|  |_______||__| |__||_______||_______||_______|#
#                                                                        #
##########################################################################

from __future__ import (absolute_import, division, print_function)

import math
import os
import sys
import time
from sqlalchemy import or_

try:
    from config import CONFIG
except:
    sys.exit()

from antshell.install import init_db
from antshell.utils.parser import load_argParser
from antshell.utils.errors import DeBug
from antshell.utils.six import PY2, PY3
from models import SESSION
from models.Hosts import Hosts
from engine import Para, Expect
from menu import Classic as Menu

if PY2:
    input = raw_input
    reload(sys)
    sys.setdefaultencoding('utf-8')
if PY3:
    from functools import reduce
DEBUG = CONFIG.DEFAULT.DEBUG


class HostView(object):
    '''
    主机交互连接处理
    '''

    def __init__(self):
        # super(Host, self).__init__()
        self.search = []
        self.check_record()
        self.HOME = os.environ["HOME"]

    @staticmethod
    def getPath(paths, L=False):
        """Absolute path generation"""
        return reduce(lambda x, y: os.path.join(x, y), paths)

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
    def __getInfo(ip, name, user, passwd, port, sudo="", bastion=0):
        '''
        获取用户相关信息
        '''

        info = {
            "name": name if name else ip,
            "ip": ip,
            "user": user if user else CONFIG.USER.USERNAME,
            "passwd": passwd if passwd else CONFIG.USER.PASSWORD,
            "port": int(port if port else CONFIG.USER.PORT),
            "sudo": sudo,
            "bastion": 1 if bastion else 0
        }
        return info

    def __editList(self, ip):
        '''
        主机信息
        '''

        ipt = self.isIp(ip, True)
        if ipt:
            hosts = self.search_hosts(include=ip, pattern=True, match=True, search=option.search)
            info = self.__getInfo(ip=ip, name=option.name, user=option.user, \
                                  passwd=option.passwd, port=int(option.port), sudo=option.sudo, bastion=option.bastion)
            DeBug(info, DEBUG)
            res = list(filter(
                lambda x: (x.user == info.get("user")) and (int(x.port) == int(info.get("port"))), hosts
            ))

            self.set_search(ip)
            return res, info
        else:
            Menu.colorMsg("wrong ip !")
            sys.exit()

    def addList(self):
        '''
        添加主机信息
        '''

        res, info = self.__editList(option.add)
        if len(res) == 1:
            Menu.colorMsg("already exist !")
        elif len(res) == 0:
            pass
            # self.hosts.insert(**info)

    def delList(self, hosts):
        '''
        删除主机信息
        '''

        delDone = False
        while not delDone:
            msg = """Confirm [ y|n ] >> """
            delDone = input(self.colorMsg(c="green", flag=True).format(msg)).upper()
            if delDone == 'Y':
                self.hosts.delete(pk=int(hosts["id"]))
                self.colorMsg("Delete IP: %s Success !" % hosts["ip"], "blue")
                delDone = True
            elif delDone == 'N':
                break
            else:
                delDone = False

    def getInfo(self, title="Title", value=None, default="", vType=str, isNone=False):
        '''
        编辑主机信息用户交互
        title: 显示标题
        value: 命令行参数值，优先于default值
        default: 默认值，原数据库中数据
        vType: 指定用户输入值
        isNone: 用户输入是否可为空，默认False，用户输入为空时使用默认值
        '''

        msg = Menu.colorMsg(c="cblue", flag=True).format("New %s [defalut: %s] >> "
                                                         % (title, value if value else default))
        while True:
            try:
                value = input(msg)
                if value == "" and not isNone:
                    value = value if value else default
                value = vType(value)
                break
            except Exception:
                pass
        return value

    def editList(self, hosts):
        editDone = False
        while not editDone:
            hosts.name = self.getInfo(title="Name", value=option.name, default=hosts.name)
            hosts.user = self.getInfo(title="User", value=option.user, default=hosts.user)
            hosts.passwd = self.getInfo(title="Passwd", value=option.passwd, default=hosts.passwd)
            hosts.port = self.getInfo(title="Port", value=option.port, default=hosts.port, vType=int)
            hosts.sudo = self.getInfo(title="Sudo", value=option.sudo, default="", isNone=True)
            hosts.bastion = self.getInfo(title="Bastion", value=option.bastion, default=hosts.bastion, vType=int)
            msg = """Confirm [ y|n ] >> """
            editDone = (input(Menu.colorMsg(c="green", flag=True).format(msg)).upper() == "Y")
        # newHost = self.__getInfo(ip=hosts.ip, name=name, user=user, \
        #                          passwd=passwd, port=int(port), sudo=sudo, bastion=bastion)
        DeBug(hosts, DEBUG)
        # self.hosts.update(pk=int(hosts.id), hosts=newHost)
        Menu.print(hosts=[hosts, ])

    def check_record(self):
        host = self.search_hosts()
        if not host:
            print("Please Add Host Record!")
            sys.exit()

    def set_search(self, search):
        if search and (search not in self.search):
            self.search.append(search)

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
        Menu.Hlen = len(hosts)
        return hosts

    def view(self):
        '''
        用户交互形式选定主机
        '''
        if option.v:
            try:
                option.num = int(option.v)
            except Exception:
                self.set_search(option.v)

        hosts = self.search_hosts(search=option.search)
        option.num = 1 if Menu.Hlen == 1 else option.num
        Menu.title()

        if not option.num:

            Menu.print(hosts=hosts, cmode=option.mode)
            default_page = int(CONFIG.DEFAULT.PAGE)
            limit, offset = 0, int(default_page if default_page != 0 else 15)

            while not option.num:
                try:
                    msg = """\nInput your choose or [ 'q' | ctrl-c ] to quit!\nServer [ ID | IP | NAME ] >> """
                    n = input(Menu.colorMsg(c="cblue", flag=True).format(msg))
                    if n in ('q', 'Q', 'quit', 'exit'):
                        sys.exit()
                    elif n in ('c', 'C', 'clear'):
                        option.search = ""
                        self.search = []
                        hosts = self.search_hosts(search=option.search)
                    elif n in ('n', 'N'):
                        limit = (limit - 1) if limit > 1 else 1
                    elif n in ('m', 'M'):
                        limit = (limit + 1)
                    else:
                        try:
                            option.num = int(n) if int(n) <= Menu.Hlen else 0
                        except Exception:
                            if n:
                                self.set_search(n)
                                hosts = self.search_hosts(search=option.search)
                            else:
                                limit = (limit + 1)
                        option.num = 1 if Menu.Hlen == 1 else option.num
                    if option.num:
                        break
                except EOFError as e:
                    print("\r")
                except KeyboardInterrupt as e:
                    sys.exit("\r")
                Menu.print(hosts=hosts, limit=limit, offset=offset, flag=False)
        DeBug(hosts, DEBUG)
        return hosts[option.num - 1]


def main():
    """主函数"""

    global option

    parser = load_argParser()
    option = parser.parse_args()

    try:
        if option.init:
            init_db()
            sys.exit()

        h = HostView()
        if option.list:
            hosts = h.search_hosts()
            Menu.print(hosts=hosts, cmode=option.mode)
            sys.exit()
        elif option.add:
            h.addList()
        # # elif option.para or option.get or option.put:
        # #     h.mygevent(option)

        host = h.view()
        Menu.title()
        Menu.print(hosts=[host, ])
        if option.edit:
            h.editList(hosts=host)
        elif option.delete:
            h.delList(hosts=host)
        else:
            ENGINE = option.engine if option.engine else CONFIG.DEFAULT.ENGINE
            if ENGINE == "expect":
                engine = Expect
            elif ENGINE == "paramiko":
                engine = Para
            else:
                sys.exit()
            engine.get_connect(host, agent=option.agent, sudo=option.sudo)

    except Exception as e:
        print(e)
    finally:
        sys.exit()


if __name__ == "__main__":
    main()
