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
from antshell.base import TqdmBar
from gevent import monkey
import gevent
import paramiko
import datetime
import sys

monkey.patch_all()


class ParaTools(object):
    """批量操作"""

    def paraComm(self, k, p, ch, cmds):
        """远程执行命令"""

        res = {"ip":k.get("ip"),"cmds":{}}
        for cmd in cmds:
            if k["sudo"] == '1' and k["user"] != "root":
                cmd = "sudo " + cmd
            stdin, stdout, stderr = p.exec_command(cmd)
            res["cmds"][cmd] = [x for x in stdout.readlines()]
            if stderr.read():
                buff = ""
                while not buff.endswith("# "):
                    buff = bytes.decode(ch.recv(9999))
                ch.send(cmd + "\n")
                buff = ""
                while not buff.endswith("# "):
                    buff = bytes.decode(ch.recv(9999))
                for line in buff.strip().split("\n"):
                    if (cmd not in line) and ("]#" not in line):
                        print("\t" + line)
        p.close()
        return res

    def paraSftp(self, sftp, k, option):
        """远程文件传输"""

        self.colorMsg("%s start >>>" % k["ip"], c = "blue")
        try:
            file_name = option.file if option.file else os.path.basename(
                option.get)
            if option.get:
                remotepath = self.getPath([option.get, file_name])
                localpath = self.getPath([self.base_path, file_name])
                self.colorMsg("  remote path : " + remotepath +
                              "  >>>  local path : " + localpath, "yellow")
                with TqdmBar(unit='B', unit_scale=True, miniters=1,desc=" "*8 + file_name) as t:
                    sftp.get(remotepath, localpath, callback=t.update_to)
                print("\t下载文件成功")
            elif option.put:
                localpath = self.getPath([self.base_path, option.file])
                remotepath = self.getPath([option.put, option.file])
                self.colorMsg("  local path : " + localpath +
                              "  >>>  remote path : " + remotepath, "yellow")
                with TqdmBar(unit='B', unit_scale=True, miniters=1,desc=" "*8 + file_name) as t:
                    sftp.put(localpath, remotepath, callback=t.update_to)
                print('\t上传文件成功')
        except Exception as e:
            self.colorMsg('%s\t 运行失败,失败原因\r\n\t%s' % (k["ip"], e))

    def para(self, k, r, option):
        """采用paramiko模块执行"""

        try:
            ssh = self.get_connection(k=k)
            tran = ssh.get_transport()
            if option.get or option.put:
                sftp = tran.open_sftp_client()
                self.paraSftp(sftp, k, option)
            elif option.commod:
                ch = ssh.invoke_shell()
                ch.settimeout(5)
                cmds = self.getArgs(option.commod, option.fs)
                res = self.paraComm(k, ssh, ch, cmds)
                r.append(res)
        except Exception as e:
            self.colorMsg('%s error >>>\r\n\t%s' % (k["ip"], e))

    def mygevent(self, option):
        """协程方式处理并行任务"""
        if option.v:
            try:
                option.num = int(option.v)
            except Exception as e:
                self.search.append(option.v)
        if option.search:
            self.search.append(option.search)
        pc = self.searchHost()
        pc = [
            pc[option.num - 1],
        ] if option.num else pc
        self.colorMsg("=== Starting %s ===" % datetime.datetime.now())
        res_list = []
        tasks = [gevent.spawn(self.para, x, res_list, option) for x in pc]
        gevent.joinall(tasks)
        for info in res_list:
            self.colorMsg("%s start >>>" % info["ip"], "blue")
            for c in info["cmds"]:
                self.colorMsg("  exec commod : " + c, "yellow")
                for line in info["cmds"][c]:
                    self.colorMsg("\t" + line.strip("\n"), "green")
        self.colorMsg("=== Ending %s ===" % datetime.datetime.now())
        sys.exit()