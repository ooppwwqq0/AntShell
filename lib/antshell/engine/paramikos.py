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
import paramiko
import datetime, time
import sys
import os
import fcntl, errno, signal, socket, select
import getpass
from binascii import hexlify
# from gevent import monkey
# import gevent

from antshell.utils.tqdm import TqdmBar
from antshell.bastion import GetBastionConfig, GetPasswdByTotp
from antshell.config import CONFIG
from antshell.engine.engine import Engine

try:
    import termios
    import tty
except ImportError:
    time.sleep(3)
    sys.exit()

# monkey.patch_all()

DEBUG = CONFIG.DEFAULT.DEBUG


class ParaEngine(Engine):
    '''
    paramiko操作封装
    '''

    def auth_key(self):
        '''
        获取本地private_key
        '''
        key_path = os.path.expanduser(CONFIG.DEFAULT.KEY_PATH)
        if key_path and os.path.isfile(key_path):
            try:
                key = paramiko.RSAKey.from_private_key_file(key_path)
            except paramiko.PasswordRequiredException:
                passwd = getpass.getpass["Password:"]
                key = paramiko.RSAKey.from_private_key_file(key_path, passwd)
        else:
            return False
        return key

    @staticmethod
    def agent_auth(transport, username):

        agent = paramiko.Agent()
        agent_keys = agent.get_keys()
        if len(agent_keys) == 0:
            return

        for key in agent_keys:
            print('Trying ssh-agent key %s' % hexlify(key.get_fingerprint()), )
            try:
                transport.auth_publickey(username, key)
                print('... success!')
                return
            except paramiko.SSHException:
                print('... nope.')

    def get_connection(self, k):
        """
        获取连接成功后的ssh
        """
        ssh = paramiko.SSHClient()
        # ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            pkey = self.auth_key()
            BASTION = k.bastion
            if BASTION:
                bastion = GetBastionConfig()

                ssh.connect(
                    hostname=bastion.get("host"),
                    port=int(bastion.get("port")),
                    username=bastion.get("user"),
                    password=bastion.get("passwd"),
                    allow_agent=True,
                    look_for_keys=False)
            elif pkey:
                ssh.connect(
                    hostname=k.ip,
                    port=int(k.port),
                    username=k.user,
                    password=k.passwd,
                    pkey=pkey,
                    allow_agent=True,
                    look_for_keys=True)
            return ssh
        except Exception as e:
            raise e

    @staticmethod
    def paraComm(k, p, ch, cmds):
        """远程执行命令"""

        res = {"ip": k.ip, "cmds": {}}
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

        self.colorMsg("%s start >>>" % k["ip"], c="blue")
        try:
            file_name = option.file if option.file else os.path.basename(
                option.get)
            if option.get:
                remotepath = self.getPath([option.get, file_name])
                localpath = self.getPath([self.base_path, file_name])
                self.colorMsg("  remote path : " + remotepath +
                              "  >>>  local path : " + localpath, "yellow")
                with TqdmBar(unit='B', unit_scale=True, miniters=1, desc=" " * 8 + file_name) as t:
                    sftp.get(remotepath, localpath, callback=t.update_to)
                print("\t下载文件成功")
            elif option.put:
                localpath = self.getPath([self.base_path, option.file])
                remotepath = self.getPath([option.put, option.file])
                self.colorMsg("  local path : " + localpath +
                              "  >>>  remote path : " + remotepath, "yellow")
                with TqdmBar(unit='B', unit_scale=True, miniters=1, desc=" " * 8 + file_name) as t:
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
            except Exception:
                self.search.append(option.v)
        if option.search:
            self.search.append(option.search)
        pc = self.searchHost()
        pc = [
            pc[option.num - 1],
        ] if option.num else pc
        print(pc)
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

    def posix_shell(self, k, agent, sudo):
        """
        Use paramiko channel connect server interactive.
        使用paramiko模块的channel，连接后端，进入交互式
        """
        old_tty = termios.tcgetattr(sys.stdin)
        pre_timestamp = time.time()
        data = ''
        input_mode = False
        sudo_mode = False if agent else True
        bastion_mode = True
        lang_mode = True
        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            self.channel.settimeout(0.0)

            while True:
                try:
                    r, w, e = select.select([self.channel, sys.stdin], [], [])
                    flag = fcntl.fcntl(sys.stdin, fcntl.F_GETFL, 0)
                    fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL,
                                flag | os.O_NONBLOCK)
                except Exception:
                    pass
                # 接收返回输出到屏幕
                if self.channel in r:
                    try:
                        x = self.channel.recv(1024)
                        if len(x) == 0:
                            break
                        index = 0
                        len_x = len(x)
                        if x == b'sudo -iu\r\n' and not sudo_mode:
                            continue
                        if x == b'export LANG=en_US.UTF-8;export LC_ALL=en_US.UTF-8;export LC_CTYPE=en_US.UTF-8\r\n' and not lang_mode:
                            continue
                        while index < len_x:
                            try:
                                n = os.write(sys.stdout.fileno(), x[index:])
                                sys.stdout.flush()
                                index += n
                            except OSError as msg:
                                if msg.errno == errno.EAGAIN:
                                    continue

                        self.vim_data += str(x)
                        if input_mode:
                            data += str(x)
                    except socket.timeout:
                        pass
                # 堡垒机模式
                if k.bastion == 1 and bastion_mode:
                    self.channel.send(k.ip + " " + str(k.port) + "\r")
                    bastion_mode = False
                elif lang_mode:
                    self.channel.send("export LANG=en_US.UTF-8;export LC_ALL=en_US.UTF-8;export LC_CTYPE=en_US.UTF-8\r")
                    lang_mode = False
                # sudo模式
                elif k.sudo and sudo_mode:
                    sudo_user = sudo if sudo else k.sudo
                    self.channel.send("sudo -iu " + sudo_user + "\r")
                    sudo_mode = False
                # 接收用户输入发送到server
                if sys.stdin in r:
                    try:
                        x = os.read(sys.stdin.fileno(), 8192)
                    except OSError:
                        pass
                    input_mode = True
                    if self.is_output(str(x)):
                        # 如果len(str(x)) > 1 说明是复制输入的
                        if len(str(x)) > 1:
                            data = x
                        match = self.vim_end_pattern.findall(self.vim_data)
                        if match:
                            if self.vim_flag or len(match) == 2:
                                self.vim_flag = False
                            else:
                                self.vim_flag = True
                        elif not self.vim_flag:
                            self.vim_flag = False
                            data = self.deal_command(data)[0:1024]
                        data = ''
                        self.vim_data = ''
                        input_mode = False
                    if len(x) == 0:
                        break
                    self.channel.send(x)
        except Exception as e:
            raise e
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)

    def get_connect(self, k, agent, sudo):
        """
        连接服务器
        """
        # 发起ssh连接请求 Make a ssh connection
        # paramiko.util.log_to_file("/tmp/paramiko.log")
        ssh = self.get_connection(k=k)

        tran = ssh.get_transport()
        tran.set_keepalive(30)
        tran.use_compression(True)

        # 获取连接的隧道并设置窗口大小 Make a channel and set windows size
        win_size = self.get_win_size()
        self.channel = channel = tran.open_session()
        paramiko.agent.AgentRequestHandler(self.channel)
        self.channel.get_pty(
            term='xterm', height=win_size[0], width=win_size[1])
        self.channel.invoke_shell()
        self.channel.keep_this = self.channel
        try:
            signal.signal(signal.SIGWINCH, self.set_win_size)
        except:
            pass

        self.posix_shell(k=k, agent=agent, sudo=sudo)

        channel.close()
        tran.close()


Para = ParaEngine()
