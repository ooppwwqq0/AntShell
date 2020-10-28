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

import os, sys

try:
    from antshell.config import CONFIG
except:
    sys.exit()

from antshell.install import init_db
from antshell.utils.parser import load_argParser
from antshell.utils.errors import DeBug
from antshell.utils.six import PY2
from antshell.models import SESSION, Hosts
from antshell.engine import Para, Expect
from antshell.menu import Classic as Menu

if PY2:
    input = raw_input
    reload(sys)
    sys.setdefaultencoding('utf-8')

DEBUG = CONFIG.DEFAULT.DEBUG


class HostView(object):
    '''
    主机交互连接处理
    '''

    def __init__(self):
        self.check_record()
        self.HOME = os.environ["HOME"]

    def addList(self):
        '''
        添加主机信息
        '''
        if self.isIp(option.add, True):
            Menu.set_search(option.add)
            hosts = SESSION.query(Hosts).filter_by(
                ip=option.add, user=option.user if option.user else CONFIG.USER.USERNAME,
                port=int(option.port if option.port else CONFIG.USER.PORT)).first()
            if hosts:
                Menu.colorMsg("already exist !")
            else:
                new_host = Hosts(
                    ip=option.add, sudo=option.sudo, bastion=1 if option.bastion else 0,
                    name=option.name if option.name else option.add,
                    user=option.user if option.user else CONFIG.USER.USERNAME,
                    passwd=option.passwd if option.passwd else CONFIG.USER.PASSWORD,
                    port=int(option.port if option.port else CONFIG.USER.PORT),
                )
                SESSION.add(new_host)
                SESSION.commit()
        else:
            Menu.colorMsg("wrong ip !")
            sys.exit()

    def delList(self, hosts):
        '''
        删除主机信息
        '''

        delDone = False
        while not delDone:
            msg = """Confirm [ y|n ] >> """
            delDone = input(Menu.colorMsg(c="green", flag=True).format(msg)).upper()
            if delDone == 'Y':
                SESSION.delete(hosts)
                Menu.colorMsg("Delete IP: %s Success !" % hosts.ip, "blue")
                SESSION.commit()
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

        msg = Menu.colorMsg(c="cblue", flag=True).format(
            "New %s [defalut: %s] >> " % (title, value if value else default)
        )
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
        DeBug(hosts, DEBUG)
        SESSION.commit()
        Menu.print(hosts=[hosts, ])

    @staticmethod
    def check_record():
        host = Menu.search_hosts()
        if not host:
            print("Please Add Host Record!")
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

        h = HostView()
        if option.list:
            hosts = h.search_hosts()
            Menu.print(hosts=hosts, cmode=option.mode)
            sys.exit()
        elif option.add:
            h.addList()
        # # elif option.para or option.get or option.put:
        # #     h.mygevent(option)

        host = Menu.view(option.v, option.num, option.search, option.mode, int(CONFIG.DEFAULT.PAGE))
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
