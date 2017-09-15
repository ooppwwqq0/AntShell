#!/usr/bin/env python3
# -*- coding:utf-8 -*-

#######################################################################
#                            ADAM AUTOSSH                             #
#######################################################################

# 开启兼容 python2
from __future__ import print_function
import os, sys
import datetime, time, threading
import yaml, sh, stat, re
import pexpect, paramiko
from tqdm import tqdm
from optparse import OptionParser

# python2 请开启
ver = sys.version.split(".")[0]
if ver == "2":
    reload(sys)
    sys.setdefaultencoding('utf-8')

class BaseHandle(object):
    """处理配置文件以及共用参数"""

    def __init__(self):
        """初始化"""

        CONF = "profile/adam/conf.yml"
        self.HOME = os.environ['HOME']
        yf = open(self.getPath(CONF))
        self.conf = yaml.load(yf)
        self.o = self.par(self.conf)
        self.sshfile = self.getPath(self.conf["ODB_FILE"])
        self.kfile = self.getPath(self.conf["K_FILE"])
        self.rows, self.columns = os.popen("stty size","r").read().split()
        self.Red = "\033[1;31m{0}\033[0m"
        self.Yel = "\033[1;33m{0}\033[0m"
        self.Blue = "\033[1;34m{0}\033[0m"
        self.Pink = "\033[1;35m{0}\033[0m"
        self.Lblue = "\033[1;36m{0}\033[0m"
        self.ColorSign = self.Red.format("#")

    def oldGetHost(self, include = None, pattern = False, match = False):
        """获取主机信息,old数据
            include : 用于过滤列表
            pattern : 开启返回空字典，默认False（不返回）
            match : 开启精确匹配模式，默认False（模糊匹配）
        """

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
                    try:
                        for ic in includes:
                            if match:
                                if ic != lines[1]:
                                    raise Continue()
                            elif len(lines) > 1:
                                if ic not in lines[1] and ic not in lines[0]:
                                    raise Continue()
                            else:
                                raise Continue()
                    except Continue:
                        continue
                    nhost[ikey] = dict(zip(host_key, lines))
                    ikey += 1
        if len(nhost) != 0 or pattern:
            return nhost
        return ahost

    def getPath(self, *args):
        """生成绝对路径"""

        path = self.HOME
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

    def par(self, k):
        """动态生成类+属性"""
        class o : pass
        for key in k:
            if str(type(k[key])) == "<type 'dict'>":
                setattr(o, key, self.par(k[key]))
            else:
                setattr(o, key, k[key])
        return o

class Continue(Exception):
    """处理跳出循环"""
    pass

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

    def progress_bar(self, transferred, toBeTransferred, suffix=''):
        #print("Transferred: {0}\tOut of: {1}".format(transferred, toBeTransferred))
        bar_len = 60
        filled_len = int(round(bar_len * transferred/float(toBeTransferred)))
        percents = round(100.0 * transferred/float(toBeTransferred), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.flush()
        sys.stdout.write('\t[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))

class HostHandle(BaseHandle):
    """处理主机列表"""

    def __init__(self):
        BaseHandle.__init__(self)

    def addList(self):
        """添加主机信息"""
        ipt = self.isIp(option.add, True)
        if ipt:
            ip = option.add
            res = self.oldGetHost(ip, True, True)

            if len(res) == 1:
                print(self.Red.format("already exist !"))
            elif len(res) == 0:
                u = self.conf["USERINFO"]
                record = "{0}|{0}|{1}|{2}|{3}|1".format(ip, u["USER"], u["PASS"], u["PORT"])
                with open(self.sshfile, 'a') as ahost:
                    ahost.write(record + "\n")
            else:
                print(res)
                sys.exit()
            return self.oldGetHost(ip, True, False)
        else:
            print(self.Red.format("wrong ip !"))
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
                print(self.Red.format("ip %s not exist !" % ip))
            else:
                print(res)
        else:
            print(self.Red.format("wrong ip !"))
        sys.exit()

class InfoHandle(BaseHandle):
    """主机交互列表"""

    def __init__(self, hinfo):
        BaseHandle.__init__(self)
        self.mode = option.mode
        self.hinfo = hinfo
        self.Hlen = len(self.hinfo)

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
        CenterLine = self.ColorSign + self.Red + self.ColorSign
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
                print("input num or [ 'q' | ctrl-c ] to quit!")
                #n = raw_input("Server Id: ")
                n = input("Server Id: ")
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

class ConnHandle(BaseHandle):
    """处理连接主机"""

    def __init__(self, hinfo):
        BaseHandle.__init__(self)
        self.ox = self.conf["XFILE"]
        self.hinfo = hinfo
        self.Hlen = len(self.hinfo)

    def fastConn(self):
        """处理快速连接主机方法"""

        os.chmod(self.ox,+stat.S_IRWXU)
        os.system(self.ox)

    def oldConn(self, **k):
        """采用expect的方式登录"""

        s_file = k["ip"] + "-" + k["port"] + "-" + k["user"]
        spath = self.getPath(".ssh/", s_file)
        with open(self.ox, 'w') as l_file:
            l_file.write("#!/usr/bin/expect -f\n")
            l_file.write("set timeout 30\n")
            l_file.write("spawn ssh -p%s -l %s %s\n" % (k["port"], k["user"], k["ip"]))
            try:
                if not sh.grep(k["ip"],self.kfile):
                    pass
            except Exception as e:
                l_file.write('expect "(yes/no)?"\n')
                l_file.write("send   yes\\r\n")
            if k["passwd"] and not os.path.isfile(spath):
                l_file.write('expect "password:"\n')
                l_file.write("send   %s\\r\n" %k["passwd"])
            if k["sudo"] == '1' and k["user"] != "root":
                l_file.write('expect "@"\n')
                l_file.write('send   "sudo su - \\r"\n')
            l_file.write('interact\n')
        self.fastConn()

    def exsend(self, e, line):
        e.logfile = None
        e.sendline(line)
        e.logfile = sys.stdout.buffer

    def exConn(self, **k):
        """采用pexcept模块执行"""

        ec = "ssh -p%s -l %s %s" % (k["port"], k["user"], k["ip"])
        e = pexpect.spawn(ec)
        e.logfile = sys.stdout.buffer
        flag = True
        try:
            while flag:
                i = e.expect(["continue connecting (yes/no)?", "password: ", ".*[\$#]"])
                if i == 0:
                    self.exsend(e, "yes")
                if i == 1:
                    self.exsend(e, str(k["passwd"]))
                if i == 2:
                    if k["sudo"] == '1' and k["user"] != "root":
                        self.exsend(e, "sudo su -")
                    if option.commod:
                        cmds = self.getArgs(option.commod)
                        for c in cmds:
                            self.exsend(e, c)
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

    def getConn(self, n = None):
        """处理生成登陆信息"""

        v = sys.argv
        if len(v) > 1 and "-" not in v[1]:
            if v[1] == "!" and os.path.isfile(self.ox):
                self.fastConn()
            elif v[1] == "$":
                num = int(max(self.hinfo))
            elif v[1] == '^':
                num = 1
            else:
                try:
                    num = int(v[1])
                except Exception as e:
                    self.hinfo = self.oldGetHost(v[1])
                    num = 0 if len(self.hinfo) > 1 else 1
        elif self.Hlen:
            num = 1 if self.Hlen == 1 else 0
        if n:
            num = n if n <= self.Hlen else 0
        if num == 0:
            num = InfoHandle(self.hinfo).chooHost(hlen = self.Hlen)
        choose = {1:self.hinfo[num]}
        return choose

class ParaHandle(BaseHandle):
    """paramiko"""

    def __init__(self):
        BaseHandle.__init__(self)
        self.base_path = os.getcwd()

    def auth_key(self):
        """获取本地private_key"""
        key_path = self.getPath(self.conf["KEY_PATH"])
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
            print(self.Yel.format("  exec commod : " + cmd))
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
                        buff = ch.recv(9999)
                ch.send(cmd+"\n")
                time.sleep(0.3)
                buff = ""
                while not buff.endswith("# "):
                    buff = ch.recv(9999)
                for line in buff.strip().split("\n"):
                    if (cmd not in line) and ("]#" not in line):
                        print("\t" + line)

    def paraSftp(self, k, sftp):
        """远程文件传输"""

        print(self.Lblue.format("%s start" % k["ip"]))
        try:
            file_name = option.file if option.file else  os.path.basename(option.get)
            if option.get:
                remotepath = self.getPath(option.get, file_name)
                localpath = self.getPath(self.base_path, file_name)
                print(self.Yel.format("  remote path : " + remotepath + "  >>>  local path : " + localpath))
                with tqdm(unit_scale=True, miniters=1 ,desc=" "*8 + file_name) as t:
                    p = ProgHandle(t)
                    sftp.get(remotepath, localpath, callback = p.progressBar)
                print("\t下载文件成功")
            elif option.put:
                localpath = os.path.join(self.base_path, option.file)
                remotepath = self.getPath(option.put, option.file)
                print(self.Yel.format("  local path : " + localpath + "  >>>  remote path : " + remotepath))
                with tqdm(unit_scale=True, miniters=1 ,desc=" "*8 + file_name) as t:
                    p = ProgHandle(t)
                    sftp.put(localpath, remotepath, callback = p.progressBar)
                print('\t上传文件成功')
        except Exception as e:
            print(self.Red.format('%s\t 运行失败,失败原因\r\n\t%s' % (k["ip"], e)))

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
                print(self.Red.format('%s\t 运行失败,失败原因\r\n\t%s' % (k["ip"], e)))
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
                print(self.Red.format('%s\t 运行失败,失败原因\r\n\t%s' % (k["ip"], e)))
            finally:
                p.close()
        else:
            sys.exit()

        """远程文件传输"""

class Myoption(OptionParser,BaseHandle):

    def _lang(self):
        BaseHandle.__init__(self)
        self.langset = self.conf["LANG"]["SET"]
        self.lang = self.conf["LANG"][self.langset]

    def _add_help_option(self):
        self._lang()
        self.add_option("-h", "--help",action="help",
                        help="%s" %self.lang["help"])

    def _add_version_option(self):
        self._lang()
        self.add_option("-v", "--version",action="version",
                        help="%s" %self.lang["version"])

class Parser(BaseHandle):
    """参数设置"""

    def __init__(self):
        BaseHandle.__init__(self)
        self.langset = self.conf["LANG"]["SET"]
        self.lang = self.conf["LANG"][self.langset]

    def Parserx(self):
        MSG_HELP = "%prog [OPTIONS]"
        version = "%%prog %s" %self.conf["VERSION"]
        if self.langset == "zh":
            parser = Myoption(usage = MSG_HELP, version=version)
        else:
            parser = OptionParser(usage = MSG_HELP, version=version)

        parser.add_option("-a", "--add", dest="add", action="store", type="string",
                          help="%s" %self.lang["add"], default="", metavar="ip")
        parser.add_option("-c", "--commod", dest="commod", action="store", type="string",
                          help="%s" %self.lang["commod"], default="", metavar="'cmd1,cmd2,...'")
        parser.add_option("-e", "--edit", dest="edit", action="store_true", default=False,
                          help="%s" %self.lang["edit"])
        parser.add_option("-d", "--delete", dest="dels", action="store", type="string",
                          help="%s" %self.lang["delete"], default="", metavar="ip")
        parser.add_option("-f", "--file", dest="file", action="store", type="string",
                          help="%s" %self.lang["file"], default="", metavar="file_name")
        parser.add_option("-F", "--fs", dest="fs", action="store", type="string",
                          help="%s" %self.lang["fs"], default=",", metavar="','")
        parser.add_option("-g", "--get", dest="get", action="store", type="string",
                          help="%s" %self.lang["get"], default="", metavar="file_path")
        parser.add_option("-G", "--group", dest="group", action="store", type="string",
                          help="%s" %self.lang["group"], default="", metavar="g1>g2")
        parser.add_option("-l", "--lists", dest="lists", action="store_true", default=False,
                          help="%s" %self.lang["lists"])
        parser.add_option("-m", "--mode", dest="mode", action="store", type="int",
                          help="%s" %self.lang["mode"],default="0", metavar="2")
        parser.add_option("-n", "--num", dest="num", action="store", type="int",
                          help="%s" %self.lang["num"], metavar="0")
        parser.add_option("-p", "--put", dest="put", action="store", type="string",
                          help="%s" %self.lang["put"], default="", metavar="dir_path")
        parser.add_option("-P", "--para", dest="para", action="store_true", default=False,
                          help="%s" %self.lang["para"])
        parser.add_option("-s", "--search", dest="search", action="store", type="string",
                          help="%s" %self.lang["search"], default="", metavar="ip|name")
        parser.add_option("-o", "--old", dest="old", action="store_true", default=False,
                          help="%s" %self.lang["old"])
        return parser

def main():
    """主函数"""

    base = BaseHandle()
    hinfo = base.oldGetHost(option.search)
    info = InfoHandle(hinfo)
    conn = ConnHandle(hinfo)
    host = HostHandle()
    pa = ParaHandle()

    ca = ""

    if option.lists:
        info.hostLists()
        sys.exit()
    if option.add:
        ca = host.addList()
    if option.dels:
        host.delList()

    if option.para or option.get or option.put:
        if option.search:
            pchoose = hinfo
        else:
            pchoose = ca if ca else conn.getConn(option.num)
        print(base.Red.format("=== Starting %s ===" % datetime.datetime.now()))
        threads = []
        for ki in pchoose:
            th = threading.Thread(target = pa.para(**pchoose[ki]))
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        print(base.Red.format("=== Ending %s ===" % datetime.datetime.now()))
        sys.exit()

    try:
        choose = ca if ca else conn.getConn(option.num)
        #clear = os.system('clear')
        print(choose)
        if option.old:
            conn.oldConn(**choose[1])
        else:
            conn.exConn(**choose[1])
        sys.exit()
    except Exception as e:
        print(e)
        print(parser.get_usage())

if __name__ == "__main__":
    parser = Parser().Parserx()
    (option, args) = parser.parse_args()
    main()
