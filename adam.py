#!/usr/bin/env python2
# -*- coding:utf-8 -*-

#######################################################################
#                            ADAM AUTOSSH                             #
#######################################################################

from __future__ import print_function
import os, sys
import datetime, time, threading
import yaml, sh, stat, re
import paramiko
from tqdm import tqdm
import argparse
import pyte
import struct, fcntl, signal, socket, select
try:
    import termios
    import tty
except ImportError:
    time.sleep(3)
    sys.exit()


if sys.version < '3':
    reload(sys)
    sys.setdefaultencoding('utf-8')

class GetConf(object):
    def __init__(self):
        self.CONF = "/data/profile/adam-git/conf.yml"
        self.c = self.conf(o=True)

    def _par(self, k):
        """动态生成类+属性"""
        class o : pass
        for key in k:
            if str(type(k[key])) == "<type 'dict'>":
                setattr(o, key, self._par(k[key]))
            else:
                setattr(o, key, k[key])
        return o

    def getPath(self, args, L=False):
        """生成绝对路径"""

        path = "" if L else self.HOME
        for val in args:
            path = os.path.join(path, val)
        return path

    def conf(self, k=None, o=False):
        """获取配置文件"""
        conf = yaml.load(open(self.CONF))
        conf["HOME"] = os.environ['HOME']
        conf["PWD"] = os.path.dirname(__file__)
        if o:
            return conf
        return conf[k] if k else self._par(conf)


class Tty(object):
    """
    一个虚拟终端类，实现连接ssh和记录日志，基类
    """
    def __init__(self, k, login_type='ssh'):
        self.k = k
        self.ip = None
        self.port = 22
        self.ssh = None
        self.channel = None
        self.remote_ip = ''
        self.login_type = login_type
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

    def get_log(self):
        """
        Logging user command and output.
        记录用户的日志
        """
        tty_log_dir = os.path.join(LOG_DIR, 'tty')
        date_today = datetime.datetime.now()
        date_start = date_today.strftime('%Y%m%d')
        time_start = date_today.strftime('%H%M%S')
        today_connect_log_dir = os.path.join(tty_log_dir, date_start)
        log_file_path = os.path.join(today_connect_log_dir, '%s_%s_%s' % (self.username, self.asset_name, time_start))

        try:
            mkdir(os.path.dirname(today_connect_log_dir), mode=777)
            mkdir(today_connect_log_dir, mode=777)
        except OSError:
            logger.debug('创建目录 %s 失败，请修改%s目录权限' % (today_connect_log_dir, tty_log_dir))
            raise ServerError('创建目录 %s 失败，请修改%s目录权限' % (today_connect_log_dir, tty_log_dir))

        try:
            log_file_f = open(log_file_path + '.log', 'a')
            log_time_f = open(log_file_path + '.time', 'a')
        except IOError:
            logger.debug('创建tty日志文件失败, 请修改目录%s权限' % today_connect_log_dir)
            raise ServerError('创建tty日志文件失败, 请修改目录%s权限' % today_connect_log_dir)

        if self.login_type == 'ssh':  # 如果是ssh连接过来，记录connect.py的pid，web terminal记录为日志的id
            pid = os.getpid()
            self.remote_ip = remote_ip  # 获取远端IP
        else:
            pid = 0

        log = Log(user=self.username, host=self.asset_name, remote_ip=self.remote_ip, login_type=self.login_type,
                  log_path=log_file_path, start_time=date_today, pid=pid)
        log.save()
        if self.login_type == 'web':
            log.pid = log.id  # 设置log id为websocket的id, 然后kill时干掉websocket
            log.save()

        log_file_f.write('Start at %s\r\n' % datetime.datetime.now())
        return log_file_f, log_time_f, log

    def get_connect_info(self):
        """
        获取需要登陆的主机的信息和映射用户的账号密码
        """
        asset_info = get_asset_info(self.asset)
        role_key = get_role_key(self.user, self.role)  # 获取角色的key，因为ansible需要权限是600，所以统一生成用户_角色key
        role_pass = CRYPTOR.decrypt(self.role.password)
        connect_info = {'user': self.user, 'asset': self.asset, 'ip': asset_info.get('ip'),
                        'port': int(asset_info.get('port')), 'role_name': self.role.name,
                        'role_pass': role_pass, 'role_key': role_key}
        logger.debug(connect_info)
        return connect_info

    def get_connection(self):
        """
        获取连接成功后的ssh
        """
        #connect_info = self.get_connect_info()

        c = C.c
        # 发起ssh连接请求 Make a ssh connection
        ssh = paramiko.SSHClient()
        # ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            key_path = c.get("KEY_PATH")
            if key_path and os.path.isfile(key_path):
                try:
                    ssh.connect(
                        self.k.get("ip"),
                        port=int(self.k.get("port")),
                        username=c.get("USER"),
                        password=c.get("PASS"),
                        key_filename=key_path,
                        look_for_keys=False
                    )
                    return ssh
                except (paramiko.ssh_exception.AuthenticationException, paramiko.ssh_exception.SSHException):
                    #logger.warning(u'使用ssh key %s 失败, 尝试只使用密码' % role_key)
                    pass

            ssh.connect(
                self.k.get("ip"),
                port=int(self.k.get("port")),
                username=c.get("USER"),
                password=c.get("PASS"),
                allow_agent=False,
                look_for_keys=False
            )

        except (paramiko.ssh_exception.AuthenticationException, paramiko.ssh_exception.SSHException):
            pass
        except socket.error:
            pass
        else:
            self.ssh = ssh
            return ssh


class SshTty(Tty):
    """
    一个虚拟终端类，实现连接ssh和记录日志
    """

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

    def posix_shell(self):
        """
        Use paramiko channel connect server interactive.
        使用paramiko模块的channel，连接后端，进入交互式
        """
        #log_file_f, log_time_f, log = self.get_log()
        #termlog = TermLogRecorder("wangping")
        #termlog.setid(1)
        old_tty = termios.tcgetattr(sys.stdin)
        pre_timestamp = time.time()
        data = ''
        input_mode = False
        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            self.channel.settimeout(0.0)

            while True:
                try:
                    r, w, e = select.select([self.channel, sys.stdin], [], [])
                    flag = fcntl.fcntl(sys.stdin, fcntl.F_GETFL, 0)
                    #fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flag|os.O_NONBLOCK)
                except Exception:
                    pass

                if self.channel in r:
                    try:
                        x = self.channel.recv(1024)
                        if len(x) == 0:
                            break

                        index = 0
                        len_x = len(x)
                        while index < len_x:
                            try:
                                n = os.write(sys.stdout.fileno(), x[index:])
                                sys.stdout.flush()
                                index += n
                            except OSError as msg:
                                if msg.errno == errno.EAGAIN:
                                    continue
                        now_timestamp = time.time()
                        #termlog.write(x)
                        #termlog.recoder = False
                        #log_time_f.write('%s %s\n' % (round(now_timestamp-pre_timestamp, 4), len(x)))
                        #log_time_f.flush()
                        #log_file_f.write(x)
                        #log_file_f.flush()
                        pre_timestamp = now_timestamp
                        #log_file_f.flush()

                        self.vim_data += x
                        if input_mode:
                            data += x

                    except socket.timeout:
                        pass

                if sys.stdin in r:
                    try:
                        x = os.read(sys.stdin.fileno(), 4096)
                    except OSError:
                        pass
                    #termlog.recoder = True
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
                            #if data is not None:
                                #TtyLog(log=log, datetime=datetime.datetime.now(), cmd=data).save()
                        data = ''
                        self.vim_data = ''
                        input_mode = False

                    if len(x) == 0:
                        break
                    self.channel.send(x)

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
            #log_file_f.write('End time is %s' % datetime.datetime.now())
            #log_file_f.close()
            #log_time_f.close()
            #termlog.save()
            #log.filename = termlog.filename
            #log.is_finished = True
            #log.end_time = datetime.datetime.now()
            #log.save()

    def connect(self):
        """
        Connect server.
        连接服务器
        """
        # 发起ssh连接请求 Make a ssh connection
        ssh = self.get_connection()

        transport = ssh.get_transport()
        transport.set_keepalive(30)
        transport.use_compression(True)

        # 获取连接的隧道并设置窗口大小 Make a channel and set windows size
        global channel
        win_size = self.get_win_size()
        # self.channel = channel = ssh.invoke_shell(height=win_size[0], width=win_size[1], term='xterm')
        self.channel = channel = transport.open_session()
        channel.get_pty(term='xterm', height=win_size[0], width=win_size[1])
        channel.invoke_shell()
        try:
            signal.signal(signal.SIGWINCH, self.set_win_size)
        except:
            pass

        self.posix_shell()

        # Shutdown channel socket
        channel.close()
        transport.close()
        ssh.close()


class BaseHandle(object):
    """处理配置文件以及共用参数"""

    def __init__(self):
        """初始化"""

        C = GetConf()
        self.conf = C.conf(o=True)
        self.HOME = self.conf["HOME"]
        self.PWD = self.conf["PWD"]
        self.sshfile = self.getPath([self.conf["ODB_FILE"]])
        self.kfile = self.getPath([self.conf["K_FILE"]])
        self.rows, self.columns = os.popen("stty size","r").read().split()
        self.ColorSign = self.colorMsg(flag=True).format("#")

    def colorMsg(self, m="", c="red", flag=False):
        colorSign = {
            "red" : "\033[1;31m{0}\033[0m",
            "green" : "\033[1;32m{0}\033[0m",
            "yellow" : "\033[1;33m{0}\033[0m",
            "blue" : "\033[1;34m{0}\033[0m",
            "pink" : "\033[1;35m{0}\033[0m",
            "blue" : "\033[1;36m{0}\033[0m",
        }
        msg = colorSign.get(c).format(m)
        if flag:
            return colorSign.get(c)
        else:
            print(msg)
            return msg

    def oldGetHost(self, include = None, pattern = False, match = False):
        """获取主机信息,old数据
            include : 用于过滤列表
            pattern : 开启返回空字典，默认False（不返回）
            match : 开启精确匹配模式，默认False（模糊匹配）
        """

        include = option.search if option.search else include
        if include:
            match = True if self.isIp(include, True) else match
        ahost, nhost = {}, {}
        host_key= ['name', 'ip', 'user', 'passwd', 'port', 'sudo']
        key, ikey = 1, 1
        includes = self.getArgs(include)
        with open(self.sshfile) as rhost:
            for line in rhost:
                lines = line.rstrip().rsplit('|')
                ahost[key] = dict(zip(host_key, lines))
                key += 1
        if includes:
            if match:
                res = list(filter(lambda x:ahost[x]["ip"] in includes, ahost))
            else:
                def filterNomatch(k):
                    f = list(filter(lambda x:x in ahost[k]["name"] or x in ahost[k]["ip"], includes))
                    return k if f else False
                res = list(filter(filterNomatch, ahost))
            for i in res:
                nhost[ikey] = ahost[i]
                ikey += 1
        if len(nhost) != 0 or pattern:
            return nhost
        return ahost

    def getPath(self, args, L=False):
        """生成绝对路径"""

        path = "" if L else self.HOME
        for val in args:
            path = os.path.join(path, val)
        return path

    def isIp(self, ipaddr, c = False):
        """ip匹配
            ipaddr : 需要匹配的ip
            c : ip段数匹配，默认False
        """

        q = ipaddr.strip().split('.')
        l = 4 if c else len(q)
        qi = map(int, filter(lambda x: x.isdigit(), q))
        return len(q) == l and len(list(filter(lambda x: x >= 0 and x <= 255, qi))) == l

    def getArgs(self, args):
        """参数处理
            args : 原始参数
            sepa : 分隔符，默认","
        """
        sepa = option.fs if option.fs else ","

        if args:
            cmds = args.rsplit(sepa)
            return cmds


class ProgHandle(object):
    """文件传输进度条tqdm"""

    def __init__(self, t):
        self.t = t
        self.last_b = 0

    def progressBar(self, transferred, toBeTransferred, suffix=''):
        """tqdm进度条"""
        self.t.total = toBeTransferred
        self.t.update(transferred - self.last_b)
        self.last_b = transferred


class InfoHandle(BaseHandle):
    """主机交互列表"""

    def __init__(self):
        BaseHandle.__init__(self)
        self.mode = option.mode
        self.hinfo = self.oldGetHost()
        self.Hlen = len(self.hinfo)

    def addList(self):
        """添加主机信息"""
        ipt = self.isIp(option.add, True)
        if ipt:
            ip = option.add
            res = self.oldGetHost(ip, True, True)

            if len(res) == 1:
                self.colorMsg("already exist !")
            elif len(res) == 0:
                u = self.conf["USERINFO"]
                user = option.user if option.user else u["USER"]
                passwd = option.passwd if option.passwd else u["PASS"]
                port = option.port if option.port else u["PORT"]
                sudo = 0 if passwd else 1
                record = "{0}|{0}|{1}|{2}|{3}|{4}".format(ip, user, passwd, port, sudo)
                with open(self.sshfile, 'a') as ahost:
                    ahost.write(record + "\n")
            else:
                print(res)
                sys.exit()
            return self.oldGetHost(ip, True, True)
        else:
            self.colorMsg("wrong ip !")
            sys.exit()

    def delList(self):
        """删除主机信息"""
        ipt = self.isIp(option.dels, True)
        if ipt:
            ip = option.dels
            res = self.oldGetHost(ip, True, True)

            if len(res) == 1:
                os.system("sed -i '' '/|%s|/d' %s" % (ip,self.sshfile))
                print(self.Blue.format("del ip %s success !" % ip))
            elif len(res) == 0:
                self.colorMsg("ip %s not exist !" % ip)
            else:
                print(res)
        else:
            self.colorMsg("wrong ip !")
        sys.exit()

    def hostLists(self):
        """打印主机列表"""

        count = 46
        maxm = int(int(self.columns) / count)
        Hlen = self.Hlen
        if not self.mode:
            mode = maxm if maxm < 6 else 5
        else:
            mode = self.mode if self.mode <= maxm else maxm
        mode = Hlen if Hlen < mode else mode
        n = mode * count + mode -2

        BorderLine = self.ColorSign * mode * (count + 1)
        CenterLine = self.ColorSign + self.colorMsg(flag=True) + self.ColorSign
        HeadLine = self.ColorSign + "{0}"
        TailLine = "{0}" + self.ColorSign

        clear = os.system('clear')
        print(BorderLine)
        print(CenterLine.format("[ADAM AUTO SSH]".center(n)))
        print(CenterLine.format(" ".center(n)))
        print(CenterLine.format(" ".center(n)))

        for key in self.hinfo:
            h = self.hinfo[key]
            p = ["[%s]" %str(key), h["name"], h["ip"]]
            rem = key % mode
            info_mes = "\033[1;31m{0[0]: >7}\033[0m  {0[1]: <16} - {0[2]: <17}".format(p)
            if mode == 1:
                print(CenterLine.format(info_mes.ljust(11 + n)))
            elif key == Hlen and rem == 1:
                print(CenterLine.format(info_mes.ljust(11 + n)))
            elif key == Hlen and rem != 0:
                print(TailLine.format("|"+info_mes.ljust(10 + (mode - rem) + (mode - rem + 1) * count)))
            elif rem == 1:
                print(HeadLine.format(info_mes), end=' ')
            elif rem >1:
                print("|"+info_mes, end=' ')
            else:
                print(TailLine.format("|"+info_mes))

        print(CenterLine.format(" ".center(n)))
        print(CenterLine.format(" ".center(n)))
        print(CenterLine.format("[ADAM AUTO SSH]".center(n)))
        print(BorderLine)

    def chooHost(self, num = 0, hlen = 0):
        """用户交互形式选定主机"""

        self.hostLists()
        while num == 0:
            try:
                msg = """input num or [ 'q' | ctrl-c ] to quit!\nServer Id: """
                n = input(self.colorMsg(c="green",flag=True).format(msg))
                if n == 'q':
                    sys.exit()
                else:
                    try:
                        num = int(n) if hlen and int(n) <= hlen else 0
                    except Exception as e:
                        pass
            except EOFError as e:
                print("\r")
            except KeyboardInterrupt as e:
                sys.exit("\r")
        return num

    def getConn(self, n = None):
        """处理生成登陆信息"""

        v = option.v
        if v:
            if v == "!":
                sys.exit()
            elif v == "$":
                num = int(max(self.hinfo))
            elif v == '^':
                num = 1
            else:
                try:
                    num = int(v)
                except Exception as e:
                    self.hinfo = self.oldGetHost(v)
                    num = 0 if len(self.hinfo) > 1 else 1
        elif self.Hlen:
            num = 1 if self.Hlen == 1 else 0
        if n:
            num = n if n <= self.Hlen else 0
        if num == 0:
            num = InfoHandle().chooHost(hlen = self.Hlen)
        choose = {1:self.hinfo[num]}
        return choose


class ParaHandle(BaseHandle):
    """paramiko"""

    def __init__(self):
        BaseHandle.__init__(self)
        self.hinfo = self.oldGetHost()
        self.base_path = os.getcwd()

    def auth_key(self):
        """获取本地private_key"""
        key_path = c.get("KEY_PATH")
        try:
            key = paramiko.RSAKey.from_private_key_file(key_path)
        except paramiko.PasswordRequiredException:
            passwd = getpass.getpass["RSA key password:"]
            key = paramiko.RSAKey.from_private_key_file(key_path, passwd)
        return key

    def paraComm(self, p, ch, k):
        """远程执行命令"""

        print(self.Lblue.format("%s start" % k["ip"]))
        cmds = self.getArgs(option.commod)
        for cmd in cmds:
            self.colorMsg("  exec commod : " + cmd,"yellow")
            if k["sudo"] == '1' and k["user"] != "root":
                cmd = "sudo " + cmd
            stdin, stdout, stderr = p.exec_command(cmd)
            for line in stdout.readlines():
                print("\t" + line.strip("\n"))
            if stderr.read():
                if k["sudo"] == '1' and k["user"] != "root":
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

    def paraSftp(self, k, sftp):
        """远程文件传输"""

        print(self.Lblue.format("%s start" % k["ip"]))
        try:
            file_name = option.file if option.file else  os.path.basename(option.get)
            if option.get:
                remotepath = self.getPath([option.get, file_name])
                localpath = self.getPath([self.base_path, file_name])
                self.colorMsg("  remote path : " + remotepath + "  >>>  local path : " + localpath)
                with tqdm(unit_scale=True, miniters=1 ,desc=" "*8 + file_name) as t:
                    p = ProgHandle(t)
                    sftp.get(remotepath, localpath, callback = p.progressBar)
                print("\t下载文件成功")
            elif option.put:
                localpath = os.path.join(self.base_path, option.file)
                remotepath = self.getPath([option.put, option.file])
                self.colorMsg("  local path : " + localpath + "  >>>  remote path : " + remotepath)
                with tqdm(unit_scale=True, miniters=1 ,desc=" "*8 + file_name) as t:
                    p = ProgHandle(t)
                    sftp.put(localpath, remotepath, callback = p.progressBar)
                print('\t上传文件成功')
        except Exception as e:
            self.colorMsg('%s\t 运行失败,失败原因\r\n\t%s' % (k["ip"], e))

    def para(self, **k):
        """采用paramiko模块执行"""

        if option.get or option.put:
            try:
                t = paramiko.Transport((k["ip"], int(k["port"])))
                if k["passwd"]:
                    t.connect(username=k["user"], password=k["passwd"])
                else:
                    key = self.auth_key()
                    t.connect(username=k["user"], pkey=key)
                sftp=paramiko.SFTPClient.from_transport(t)

                self.paraSftp(k, sftp)
            except Exception as e:
                self.colorMsg('%s\t 运行失败,失败原因\r\n\t%s' % (k["ip"], e))
            finally:
                t.close()
        elif option.commod:
            try:
                p = paramiko.SSHClient()
                p.load_system_host_keys()
                p.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                if k["passwd"]:
                    p.connect(hostname = k["ip"], port = int(k["port"]), username = k["user"], password =  k["passwd"], timeout = 3)
                else:
                    key = self.auth_key()
                    p.connect(hostname = k["ip"], port = int(k["port"]), username = k["user"], pkey = key, timeout = 3)
                ch = p.invoke_shell()
                ch.settimeout(5)
                self.paraComm(p, ch, k)
            except Exception as e:
                self.colorMsg('%s\t 运行失败,失败原因\r\n\t%s' % (k["ip"], e))
            finally:
                p.close()
        else:
            sys.exit()

    def thstart(self, ca = None, choose = None):
        """处理多线程任务"""

        info = InfoHandle()
        if ca:
            pchoose = ca
        elif option.search or option.num or option.args:
            pchoose = self.hinfo if len(self.hinfo) == 1 else info.getConn(option.num)
        self.colorMsg("=== Starting %s ===" % datetime.datetime.now())
        threads = []
        for ki in pchoose:
            th = threading.Thread(target = self.para(**pchoose[ki]))
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        self.colorMsg("=== Ending %s ===" % datetime.datetime.now())
        sys.exit()


class Parser(BaseHandle):
    """参数设置"""

    def __init__(self):
        BaseHandle.__init__(self)
        self.langset = self.conf["LANG"]["SET"]
        self.lang = self.conf["LANG"][self.langset]
        self.usage = """%(prog)s [-h] [--version] [-l [-m 2] ]
            [v|-n 0|-s 'ip|name' [-e] ] [-G g1>g2]
            [-P [-c 'cmd1,cmd2,...'] ] [-a ip| -d ip]
            [-f file_name [-g file_path|-p dir_path [-F ','] ] ]"""
        self.version = "%(prog)s " + self.conf["VERSION"]

    def Argparser(self):
        parser = argparse.ArgumentParser(
            prog = self.conf["PROG"],
            usage = self.usage,
            description = self.lang["desc"],
            add_help = False)

        parser.add_argument("v", nargs="?", help="%s" %self.lang["v"])
        g1 = parser.add_argument_group("sys arguments")
        g1.add_argument("-h", "--help", action="help",
                            help="%s" %self.lang["help"])
        g1.add_argument("--version", action = "version", version=self.version,
                            help="%s" %self.lang["version"])

        g2 = parser.add_argument_group("edit arguments")
        g2.add_argument("-a", "--add", dest="add", action="store", type=str,
                            help="%s" %self.lang["add"], metavar="ip")
        g2.add_argument("-e", "--edit", dest="edit", action="store_true", default=False,
                            help="%s" %self.lang["edit"])
        g2.add_argument("-d", "--delete", dest="dels", action="store", type=str,
                            help="%s" %self.lang["delete"], metavar="ip")
        g2.add_argument("--user", dest="user", action="store", type=str,
                            help="%s" %self.lang["user"], metavar="root")
        g2.add_argument("--passwd", dest="passwd", action="store", type=str,
                            help="%s" %self.lang["passwd"], metavar="xxx")
        g2.add_argument("--port", dest="port", action="store", type=int,
                            help="%s" %self.lang["port"], metavar="22")

        g3 = parser.add_argument_group("host arguments")
        g3.add_argument("-l", "--lists", dest="lists", action="store_true", default=False,
                            help="%s" %self.lang["lists"])
        g3.add_argument("-m", "--mode", dest="mode", action="store", type=int,
                            help="%s" %self.lang["mode"],default=0, metavar="2")
        g3.add_argument("-n", "--num", dest="num", action="store", type=int,
                            help="%s" %self.lang["num"], metavar=0)
        g3.add_argument("-s", "--search", dest="search", action="store", type=str,
                            help="%s" %self.lang["search"], metavar="'ip|name'")
        g3.add_argument("-G", "--group", dest="group", action="store", type=str,
                            help="%s" %self.lang["group"], metavar="g1>g2")

        g4 = parser.add_argument_group("manager arguments")
        g4.add_argument("-P", "--para", dest="para", action="store_true", default=False,
                            help="%s" %self.lang["para"])
        g4.add_argument("-c", "--commod", dest="commod", action="store", type=str,
                            help="%s" %self.lang["commod"], metavar="'cmd1,cmd2,...'")
        g4.add_argument("-f", "--file", dest="file", action="store", type=str,
                            help="%s" %self.lang["file"], metavar="file_name")
        g4.add_argument("-g", "--get", dest="get", action="store", type=str,
                            help="%s" %self.lang["get"], metavar="file_path")
        g4.add_argument("-p", "--put", dest="put", action="store", type=str,
                            help="%s" %self.lang["put"], metavar="dir_path")
        g4.add_argument("-F", "--fs", dest="fs", action="store", type=str,
                            help="%s" %self.lang["fs"], default=",", metavar="','")
        return parser


def main():
    """主函数"""

    info = InfoHandle()
    pa = ParaHandle()

    if option.lists:
        info.hostLists()
        sys.exit()
    ca = info.addList() if option.add else ""
    if option.dels:
        info.delList()

    if option.para or option.get or option.put:
        pa.thstart(ca)
    try:
        choose = ca if ca else info.getConn(option.num)
        #clear = os.system('clear')
        print(choose)
        ssh_tty = SshTty(choose[1])
        ssh_tty.connect()
        sys.exit()
    except Exception as e:
        print(e)
        print(parser.print_help())


if __name__ == "__main__":
    parser = Parser().Argparser()
    option = parser.parse_args()
    C = GetConf()
    main()
