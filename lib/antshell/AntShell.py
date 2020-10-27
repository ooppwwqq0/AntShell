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
from antshell.expect import Expect

import math
import os
import sys
import time

if PY2:
    input = raw_input
    reload(sys)
    sys.setdefaultencoding('utf-8')

DEBUG = CONFIG.DEFAULT.DEBUG


class HostHandle(ParaTools, SShTools, Expect):
    '''
    主机交互连接处理
    '''

    def __init__(self):
        super(HostHandle, self).__init__()
        self.HOME = os.environ["HOME"]
        self.hinfo = []
        self.Hlen = 0
        self.hosts = Hosts

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
            res = self.searchHost(include=ip, pattern=True, match=True, search=option.search)
            info = self.__getInfo(ip=ip, name=option.name, user=option.user, \
                passwd=option.passwd, port=int(option.port), sudo=option.sudo, bastion=option.bastion)
            DeBug(info, DEBUG)
            res = list(filter(
                lambda x:(x["user"] == info.get("user")) \
                    and (int(x["port"]) == int(info.get("port"))), res
            ))
            self.search.append(ip)
            return res, info
        else:
            self.colorMsg("wrong ip !")
            sys.exit()

    def addList(self):
        '''
        添加主机信息
        '''

        res, info = self.__editList(option.add)
        if len(res) == 1:
            self.colorMsg("already exist !")
        elif len(res) == 0:
            self.hosts.insert(**info)

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

        msg = self.colorMsg(c="cblue", flag=True).format("New %s [defalut: %s] >> " 
                %(title, value if value else default))
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
            name = self.getInfo(title="Name", value=option.name, default=hosts["name"])
            user = self.getInfo(title="User", value=option.user, default=hosts["user"])
            passwd = self.getInfo(title="Passwd", value=option.passwd, default=hosts["passwd"])
            port = self.getInfo(title="Port", value=option.port, default=hosts["port"], vType=int)
            sudo = self.getInfo(title="Sudo", value=option.sudo, default="", isNone=True)
            bastion = self.getInfo(title="Bastion", value=option.bastion, default=hosts["bastion"], vType=int)
            msg = """Confirm [ y|n ] >> """
            editDone = (input(self.colorMsg(c="green", flag=True).format(msg)).upper() == "Y" )
        newHost = self.__getInfo(ip=hosts["ip"], name=name, user=user, \
                passwd=passwd, port=int(port), sudo=sudo, bastion=bastion)
        DeBug(newHost, DEBUG)
        self.hosts.update(pk=int(hosts["id"]), hosts=newHost)
        self.printHosts(hosts=[newHost,])

    def connect(self):
        '''
        用户交互形式选定主机
        '''

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
            default_page = int(CONFIG.DEFAULT.PAGE)
            limit, offset = 0, int(default_page if default_page !=0 else 15)
            while not option.num:
                try:
                    msg = """\nInput your choose or [ 'q' | ctrl-c ] to quit!\nServer [ ID | IP | NAME ] >> """
                    n = input(self.colorMsg(c="cblue", flag=True).format(msg))
                    if n in ('q', 'Q', 'quit', 'exit'):
                        sys.exit()
                    elif n in ('c', 'C', 'clear'):
                        option.search = ""
                        self.search = []
                        hosts = self.searchHost(search=option.search)
                    elif n in ('n','N'):
                        limit = (limit - 1) if limit > 1 else 1
                    elif n in ('m','M'):
                        limit = (limit + 1)
                    else:
                        try:
                            option.num = int(n) if int(n) <= self.Hlen else 0
                        except Exception:
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
        os.system("clear")
        self.colorMsg(__banner__.lstrip("\n"), banner_color)
        DeBug(hosts, DEBUG)
        self.printHosts(hosts=[hosts,])
        if option.edit:
            self.editList(hosts=hosts)
        elif option.delete:
            self.delList(hosts=hosts)
        else:
            ENGINE = option.engine if option.engine else CONFIG.DEFAULT.ENGINE
            if ENGINE == "expect":
                self.exConn(hosts, sudo=option.sudo)
            elif ENGINE == "paramiko":
                self.get_connect(hosts, agent=option.agent, sudo=option.sudo)
            else:
                sys.exit()


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
        
        if option.list:
            h.printHosts(cmode=option.mode)
            sys.exit()
        elif option.add:
            h.addList()
        # elif option.para or option.get or option.put:
        #     h.mygevent(option)

        h.connect()
    except Exception as e:
        print(e)
    finally:
        sys.exit()


if __name__ == "__main__":
    main()
