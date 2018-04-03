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
from base import BaseToolsBox, TqdmBar, __banner__
from base import load_config, load_argParser
from install import init_db, init_conf, file_convert_to_db
from gevent import monkey
import gevent
import paramiko
import threading

monkey.patch_all()


class ParaTools(object):

    def paraComm(self, p, ch):
        """远程执行命令"""

        self.colorMsg("%s start" % self.k["ip"], "blue")
        cmds = self.getArgs(option.commod, option.fs)
        for cmd in cmds:
            self.colorMsg("  exec commod : " + cmd, "yellow")
            if self.k["sudo"] == '1' and self.k["user"] != "root":
                cmd = "sudo " + cmd
            stdin, stdout, stderr = p.exec_command(cmd)
            for line in stdout.readlines():
                print("\t" + line.strip("\n"))
            if stderr.read():
                if self.k["sudo"] == '1' and self.k["user"] != "root":
                    ch.send("sudo su - \n")
                    buff = ""
                    while not buff.endswith("# "):
                        buff = bytes.decode(ch.recv(9999))
                ch.send(cmd + "\n")
                time.sleep(0.3)
                buff = ""
                while not buff.endswith("# "):
                    buff = bytes.decode(ch.recv(9999))
                for line in buff.strip().split("\n"):
                    if (cmd not in line) and ("]#" not in line):
                        print("\t" + line)

    def paraSftp(self, sftp):
        """远程文件传输"""

        self.colorMsg("%s start" % self.k["ip"], c = "blue")
        try:
            file_name = option.file if option.file else os.path.basename(
                option.get)
            if option.get:
                remotepath = self.getPath([option.get, file_name])
                localpath = self.getPath([self.base_path, file_name])
                self.colorMsg("  remote path : " + remotepath +
                              "  >>>  local path : " + localpath, "yellow")
                with tqdm(
                        unit_scale=True, miniters=1,
                        desc=" " * 8 + file_name) as t:
                    p = TqdmBar(t)
                    sftp.get(remotepath, localpath, callback=p.progressBar)
                print("\t下载文件成功")
            elif option.put:
                localpath = self.getPath([self.base_path, option.file])
                remotepath = self.getPath([option.put, option.file])
                self.colorMsg("  local path : " + localpath +
                              "  >>>  remote path : " + remotepath, "yellow")
                with tqdm(
                        unit_scale=True, miniters=1,
                        desc=" " * 8 + file_name) as t:
                    p = TqdmBar(t)
                    sftp.put(localpath, remotepath, callback=p.progressBar)
                print('\t上传文件成功')
        except Exception as e:
            self.colorMsg('%s\t 运行失败,失败原因\r\n\t%s' % (self.k["ip"], e))

    def para(self, k):
        """采用paramiko模块执行"""

        self.k = k
        try:
            ssh = self.get_connection()
            tran = ssh.get_transport()
            if option.get or option.put:
                sftp = tran.open_sftp_client()
                self.paraSftp(sftp)
            elif option.commod:
                ch = ssh.invoke_shell()
                ch.settimeout(5)
                self.paraComm(ssh, ch)
        except Exception as e:
            self.colorMsg('%s\t 运行失败,失败原因\r\n\t%s' % (k["ip"], e))
        finally:
            tran.close()
            ssh.close()

    def thstart(self, choose=None):
        """处理多线程任务"""

        if option.v:
            try:
                option.num = int(option.v)
            except Exception as e:
                option.search = option.v
        pc = self.hinfo if self.hinfo else self.searchHost()
        pc = [
            pc[option.num - 1],
        ] if option.num else pc
        self.colorMsg("=== Starting %s ===" % datetime.datetime.now())
        threads = []
        for ki in pc:
            th = threading.Thread(target=self.para(ki))
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        self.colorMsg("=== Ending %s ===" % datetime.datetime.now())
        sys.exit()
