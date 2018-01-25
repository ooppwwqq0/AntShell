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
from base import ToolsBox, TqdmBar
from base import load_config, load_argParser
import os, sys, re
import datetime, time
import yaml
import paramiko
import ansible
import sqlite3
import pyte
import errno
import threading
import struct, fcntl, signal, socket, select
from tqdm import tqdm
try:
    import termios
    import tty
except ImportError:
    time.sleep(3)
    sys.exit()

if sys.version < '3':
    reload(sys)
    sys.setdefaultencoding('utf-8')


class Base(ToolsBox):
    """处理配置文件以及数据库操作基类"""

    def __init__(self):
        """初始化"""
        self.db = self._db()
        self.HOME = os.environ["HOME"]
        self.rows, self.columns = os.popen("stty size","r").read().split()
        self.ColorSign = self.colorMsg(flag=True).format("#")
        self.base_path = os.getcwd()
        self.hinfo = []
        self.Hlen = 0

    def _db(self):
        db_file = os.path.expanduser(conf.get("DB_FILE"))
        try:
            if db_file and os.path.isfile(db_file):
                self.conn = sqlite3.connect(db_file)
                self.conn.row_factory = self._dict_factory
                db = self.conn.cursor()
                return db
        except Exception as e:
            print(e)
        sys.exit()

    def _commit(self):
        self.conn.commit()

    def _dbclose(self):
        self.conn.close()


class SShHandler(Base):
    """ssh虚拟终端类"""

    def __init__(self):
        Base.__init__(self)
        self.ssh = None
        self.channel = None
        self.vim_flag = False
        self.vim_end_pattern = re.compile(r'\x1b\[\?1049', re.X)
        self.vim_data = ''
        self.stream = None
        self.screen = None
        self.__init_screen_stream()

    def __init_screen_stream(self):
        """
        初始化虚拟屏幕和字符流
        """
        self.stream = pyte.ByteStream()
        self.screen = pyte.Screen(80, 24)
        self.stream.attach(self.screen)

    def auth_key(self):
        """获取本地private_key"""
        key_path = os.path.expanduser(conf.get("KEY_PATH"))
        if key_path and os.path.isfile(key_path):
            try:
                key = paramiko.RSAKey.from_private_key_file(key_path)
            except paramiko.PasswordRequiredException:
                passwd = getpass.getpass["RSA key password:"]
                key = paramiko.RSAKey.from_private_key_file(key_path, passwd)
        else:
            return False
        return key

    @staticmethod
    def is_output(strings):
        newline_char = ['\n', '\r', '\r\n']
        for char in newline_char:
            if char in strings:
                return True
        return False

    @staticmethod
    def command_parser(command):
        """
        处理命令中如果有ps1或者mysql的特殊情况,极端情况下会有ps1和mysql
        :param command:要处理的字符传
        :return:返回去除PS1或者mysql字符串的结果
        """
        result = None
        match = re.compile('\[?.*@.*\]?[\$#]\s').split(command)
        if match:
            # 只需要最后的一个PS1后面的字符串
            result = match[-1].strip()
        else:
            # PS1没找到,查找mysql
            match = re.split('mysql>\s', command)
            if match:
                # 只需要最后一个mysql后面的字符串
                result = match[-1].strip()
        return result

    def deal_command(self, data):
        """
        处理截获的命令
        :param data: 要处理的命令
        :return:返回最后的处理结果
        """
        command = ''
        try:
            self.stream.feed(data)
            # 从虚拟屏幕中获取处理后的数据
            for line in reversed(self.screen.buffer):
                line_data = "".join(map(operator.attrgetter("data"), line)).strip()
                if len(line_data) > 0:
                    parser_result = self.command_parser(line_data)
                    if parser_result is not None:
                        # 2个条件写一起会有错误的数据
                        if len(parser_result) > 0:
                            command = parser_result
                    else:
                        command = line_data
                    break
        except Exception:
            pass
        # 虚拟屏幕清空
        self.screen.reset()
        return command

    def get_connection(self):
        """
        获取连接成功后的ssh
        """
        ssh = paramiko.SSHClient()
        # ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            pkey = self.auth_key()
            if pkey:
                try:
                    ssh.connect(
                        hostname=self.k.get("ip"),
                        port=int(self.k.get("port")),
                        username=self.k.get("user"),
                        password=self.k.get("passwd"),
                        pkey=pkey,
                        look_for_keys=False
                    )
                    return ssh
                except Exception as e:
                    print(e)
                    pass
            ssh.connect(
                hostname=self.k.get("ip"),
                port=int(self.k.get("port")),
                username=self.k.get("user"),
                password=self.k.get("passwd"),
                allow_agent=False,
                look_for_keys=False
            )
        except Exception as e:
            print(e)
            sys.exit()
        else:
            self.ssh = ssh
            return ssh

    @staticmethod
    def get_win_size():
        """
        获得terminal窗口大小
        """
        if 'TIOCGWINSZ' in dir(termios):
            TIOCGWINSZ = termios.TIOCGWINSZ
        else:
            TIOCGWINSZ = 1074295912
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(sys.stdout.fileno(), TIOCGWINSZ, s)
        return struct.unpack('HHHH', x)[0:2]

    def set_win_size(self, sig, data):
        """
        设置terminal窗口大小
        """
        try:
            win_size = self.get_win_size()
            self.channel.resize_pty(height=win_size[0], width=win_size[1])
        except Exception:
            pass


class HostHandle(SShHandler):
    """主机交互连接处理"""

    def searchHost(self, include = None, pattern = False, match = False):
        """获取主机信息, 基于sqlite3
            include : 用于过滤列表
            pattern : 开启返回空字典，默认False（不返回）
            match : 开启精确匹配模式，默认False（模糊匹配）
        """

        include = include if include else option.search
        match = True if self.isIp(include, True) else match
        search = self._getSearch(include, match)
        sql = """select id,name,ip,user,passwd,port,sudo
            from hosts where 1=1 {0} order by sort;"""
        self.db.execute(sql.format(search))
        hosts = [info for info in self.db]
        if not hosts and not pattern:
            self.db.execute(sql.format(""))
            hosts = [info for info in self.db]
        self.Hlen = len(hosts)
        return hosts

    def _getSearch(self, include, match, search=""):
        includes = self.getArgs(include, option.fs)
        if includes:
            if match:
                search = """and ip in ({0})""".format(
                    ",".join(list(
                        map(lambda x:"'%s'" %x, includes)
                    ))
                )
            else:
                search = """and ({0})""".format(
                    " or ".join(list(map(
                        lambda x:"name like '%%{0}%%' or ip like '%%{0}%%'".format(x), includes
                    )))
                )
        return search

    def _getInfo(self, ip):
        """获取用户相关信息"""
        self.info = {
            "name" : option.name if option.name else ip,
            "ip" : ip,
            "user" : option.user if option.user else conf.get("USER"),
            "passwd" : option.passwd if option.passwd else conf.get("PASS"),
            "port" : option.port if option.port else conf.get("PORT"),
        }
        self.info["sudo"] = 0 if self.info["user"] == "root" else 1

    def _editList(self, ip):
        """主机信息"""
        ipt = self.isIp(ip, True)
        if ipt:
            res = self.searchHost(ip, True, True)
            self._getInfo(ip)
            res = list(filter(
                lambda x:x["user"] == self.info.get("user") \
                and x["port"] == self.info.get("port"), res
            ))
            option.search = ip
            return res
        else:
            self.colorMsg("wrong ip !")
            sys.exit()

    def addList(self):
        """添加主机信息"""
        res = self._editList(option.add)
        if len(res) == 1:
            self.colorMsg("already exist !")
        elif len(res) == 0:
            sql = """insert into hosts(name,ip,user,passwd,port,sudo)
                values('{name}','{ip}','{user}','{passwd}',{port},{sudo})""".format(**self.info)
            self.db.execute(sql)
            self._commit()
        else:
            print(res)
            sys.exit()

    def delList(self):
        """删除主机信息"""
        res = self._editList(option.dels)
        if len(res) == 1:
            sql = """delete from hosts where id={0};""".format(res[0]["id"])
            self.db.execute(sql)
            self._commit()
            self.colorMsg("del ip %s success !" % option.dels,"blue")
        elif len(res) == 0:
            self.colorMsg("ip %s not exist !" % option.dels)
        else:
            print(res)
        sys.exit()

    def hostLists(self, hlist = None):
        """打印主机列表"""

        count = 46
        maxm = int(int(self.columns) / count)
        self.hinfo = self.hinfo if self.hinfo else self.searchHost()
        self.Hlen = Hlen = len(self.hinfo)
        if not option.mode:
            mode = maxm if maxm < 6 else 5
        else:
            mode = option.mode if option.mode <= maxm else maxm
        mode = Hlen if Hlen < mode else mode
        n = mode * count + mode -2
        BorderLine = self.ColorSign * mode * (count + 1)
        CenterLine = self.ColorSign + self.colorMsg(flag=True) + self.ColorSign
        HeadLine = self.ColorSign + "{0}"
        TailLine = "{0}" + self.ColorSign

        clear = os.system('clear')
        print(BorderLine)
        print(CenterLine.format("[AntShell AUTOSSH]".center(n)))
        print(CenterLine.format(" ".center(n)))
        print(CenterLine.format(" ".center(n)))

        for key in range(1, Hlen+1):
            h = self.hinfo[key-1]
            rem = key % mode
            info_mes = "{0}  {1} - {2}".format(
                self.colorMsg(c="red", flag=True).format("{0: >7}".format("[%s]" %str(key))),
                self.colorMsg(c="blue", flag=True).format("{0: <16}".format(h["name"])),
                self.colorMsg(c="green", flag=True).format("{0: <17}".format(h["ip"])),
            )
            if mode == 1:
                print(CenterLine.format(info_mes.ljust(11 + n)))
            elif key == Hlen and rem == 1:
                print(CenterLine.format(info_mes.ljust(33 + n)))
            elif key == Hlen and rem != 0:
                print(TailLine.format("|"+info_mes.ljust(33 + (mode - rem -1) + (mode - rem + 1) * count)))
            elif rem == 1:
                print(HeadLine.format(info_mes), end=' ')
            elif rem > 1:
                print("|"+info_mes, end=' ')
            else:
                print(TailLine.format("|"+info_mes))

        print(CenterLine.format(" ".center(n)))
        print(CenterLine.format(" ".center(n)))
        print(CenterLine.format("[AntShell AUTOSSH]".center(n)))
        print(BorderLine)

    def _chooHost(self, num = 0):
        """用户交互形式选定主机"""

        if option.v:
            if option.v == "!":
                sys.exit()
            elif option.v == '^':
                option.num = 1
            else:
                try:
                    option.num = int(option.v)
                except Exception as e:
                    option.search = option.v
        self.hinfo = self.searchHost()
        option.num = 1 if self.Hlen == 1 and not option.num else option.num
        if not option.num:
            self.hostLists()
            while not option.num:
                try:
                    msg = """input num or [ 'q' | ctrl-c ] to quit!\nServer Id: """
                    n = raw_input(self.colorMsg(c="green",flag=True).format(msg))
                    if n in ['q','Q','quit','exit']:
                        sys.exit()
                    else:
                        try:
                            option.num = int(n) if int(n) <=self.Hlen else 0
                        except Exception as e:
                            pass
                except EOFError as e:
                    print("\r")
                except KeyboardInterrupt as e:
                    sys.exit("\r")
        self.hinfo = self.searchHost()[option.num - 1]
        print(self.hinfo)

    def getConn(self):
        """处理生成登陆信息"""

        self._chooHost()
        return self.hinfo[option.num-1]

    def paraComm(self, p, ch, ):
        """远程执行命令"""

        self.colorMsg("%s start" % self.k["ip"],"blue")
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
                ch.send(cmd+"\n")
                time.sleep(0.3)
                buff = ""
                while not buff.endswith("# "):
                    buff = bytes.decode(ch.recv(9999))
                for line in buff.strip().split("\n"):
                    if (cmd not in line) and ("]#" not in line):
                        print("\t" + line)

    def paraSftp(self, sftp):
        """远程文件传输"""

        self.colorMsg("%s start" % self.k["ip"],"blue")
        try:
            file_name = option.file if option.file else  os.path.basename(option.get)
            if option.get:
                remotepath = self.getPath([option.get, file_name])
                localpath = self.getPath([self.base_path, file_name])
                self.colorMsg("  remote path : " + remotepath + "  >>>  local path : " + localpath, "yellow")
                with tqdm(unit_scale=True, miniters=1 ,desc=" "*8 + file_name) as t:
                    p = TqdmBar(t)
                    sftp.get(remotepath, localpath, callback = p.progressBar)
                print("\t下载文件成功")
            elif option.put:
                localpath = self.getPath([self.base_path, option.file])
                remotepath = self.getPath([option.put, option.file])
                self.colorMsg("  local path : " + localpath + "  >>>  remote path : " + remotepath, "yellow")
                with tqdm(unit_scale=True, miniters=1 ,desc=" "*8 + file_name) as t:
                    p = TqdmBar(t)
                    sftp.put(localpath, remotepath, callback = p.progressBar)
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

    def thstart(self, choose = None):
        """处理多线程任务"""

        pc = self.hinfo if self.hinfo else self.searchHost()
        pc = [pc[option.num - 1],] if option.num else pc
        self.colorMsg("=== Starting %s ===" % datetime.datetime.now())
        threads = []
        for ki in pc:
            th = threading.Thread(target = self.para(ki))
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        self.colorMsg("=== Ending %s ===" % datetime.datetime.now())
        sys.exit()

    def posix_shell(self):
        """
        Use paramiko channel connect server interactive.
        使用paramiko模块的channel，连接后端，进入交互式
        """
        old_tty = termios.tcgetattr(sys.stdin)
        pre_timestamp = time.time()
        data = ''
        input_mode = False
        sudo_mode = True
        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            self.channel.settimeout(0.0)

            while True:
                try:
                    r, w, e = select.select([self.channel, sys.stdin], [], [])
                    flag = fcntl.fcntl(sys.stdin, fcntl.F_GETFL, 0)
                    fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flag|os.O_NONBLOCK)
                except Exception:
                    pass
                if self.channel in r:
                    try:
                        x = self.channel.recv(1024)
                        if len(x) == 0:
                            break
                        index = 0
                        len_x = len(x)
                        if x == "sudo su -\r\n" and not sudo_mode:
                            continue
                        while index < len_x:
                            try:
                                n = os.write(sys.stdout.fileno(), x[index:])
                                sys.stdout.flush()
                                index += n
                            except OSError as msg:
                                if msg.errno == errno.EAGAIN:
                                    continue
                        self.vim_data += x
                        if input_mode:
                            data += x
                    except socket.timeout:
                        pass
                if self.k["sudo"] == 1 and self.k["user"] != "root" and sudo_mode:
                    self.channel.send("sudo su -\r")
                    sudo_mode = False
                if sys.stdin in r:
                    try:
                        x = os.read(sys.stdin.fileno(), 4096)
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
                            data = self.deal_command(data)[0:200]
                        data = ''
                        self.vim_data = ''
                        input_mode = False
                    if len(x) == 0:
                        break
                    self.channel.send(x)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)

    def connect(self):
        """
        连接服务器
        """
        self._chooHost()
        self.k = self.hinfo
        # 发起ssh连接请求 Make a ssh connection
        ssh = self.get_connection()

        tran = ssh.get_transport()
        tran.set_keepalive(30)
        tran.use_compression(True)

        # 获取连接的隧道并设置窗口大小 Make a channel and set windows size
        win_size = self.get_win_size()
        self.channel = channel = tran.open_session()
        channel.get_pty(term='xterm', height=win_size[0], width=win_size[1])
        channel.invoke_shell()
        try:
            signal.signal(signal.SIGWINCH, self.set_win_size)
        except:
            pass

        self.posix_shell()

        channel.close()
        tran.close()


def main():
    """主函数"""
    global option
    global conf
    conf = load_config()
    parser = load_argParser()
    option = parser.parse_args()

    h = HostHandle()
    try:
        if option.lists:
            h.hostLists()
            sys.exit()
        elif option.dels:
            h.delList()
        elif option.add:
            h.addList()
        elif option.para or option.get or option.put:
            h.thstart()
        #clear = os.system('clear')
        h.connect()
    except Exception as e:
        print(e)
        print(parser.print_help())
    finally:
        print("close connect")
        h._dbclose()
        sys.exit()


if __name__ == "__main__":
    main()
