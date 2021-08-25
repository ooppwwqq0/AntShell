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
import pexpect
import time
import sys

from antshell.bastion import GetBastionConfig, GetPasswdByTotp
from antshell.config import CONFIG
from antshell.engine.engine import Engine

try:
    import termios
    import tty
except ImportError:
    time.sleep(3)
    sys.exit()

DEBUG = CONFIG.DEFAULT.DEBUG


class ExpectEngine(Engine):
    """处理连接主机"""

    def exsend(self, e, line):
        e.logfile = None
        e.sendline(line)
        e.logfile = sys.stdout.buffer

    def get_connect(self, k, agent, sudo):
        """采用pexcept模块执行"""
        BASTION = k.get("bastion")
        if BASTION:
            bastion = GetBastionConfig()
            ec = "ssh -p{port} -l {user} {host}".format(
                port=bastion.get("port"),
                user=bastion.get("user"),
                host=bastion.get("host"))
            password = bastion.get("passwd")
        else:
            ec = "ssh -p{port} -l {user} {host}".format(
                port=k.get("port"),
                user=k.get("user"),
                host=k.get("ip"))
            password = k.get("passwd")
        e = pexpect.spawn(ec)
        e.logfile = sys.stdout.buffer
        flag = True
        bastion_mode = True
        sudo_mode = True
        try:
            while flag:
                i = e.expect(["continue connecting (yes/no)?", "[P|p]assword: ", ":", ".*[\$#~]"])

                if i == 0:
                    self.exsend(e, "yes")
                if i == 1:
                    self.exsend(e, str(password))
                if i == 2:
                    # 堡垒机模式
                    if k.get("bastion") == 1 and bastion_mode:
                        self.exsend(e, k.get("ip") + " " + str(k.get("port")))
                        bastion_mode = False
                if i == 3:
                    # sudo模式
                    if k.get("sudo") and sudo_mode:
                        sudo_user = sudo if sudo else k.get("sudo")
                        self.exsend(e, "sudo -iu " + sudo_user)
                        sudo_mode = False
                    # if option.commod:
                    #     cmds = self.getArgs(option.commod)
                    #     for c in cmds:
                    #         self.exsend(e, c)
                    flag = False
            e.logfile = None
            e.setwinsize(int(self.rows), int(self.columns))
            e.interact(chr(29))
        except pexpect.EOF:
            print("EOF")
        except pexpect.TIMEOUT:
            print("TIMEOUT")
        finally:
            e.close()


Expect = ExpectEngine()
