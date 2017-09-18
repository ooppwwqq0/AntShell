#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from antshell.release import __prog__, __version__
from antshell.lang import LANG
import os
import sys
import yaml
import argparse


class ToolsBox(object):

    """base tools class"""

    def _par(self, k):
        """dynamic generation class and add attribute"""
        class o : pass
        for key in k:
            if str(type(k[key])) == "<type 'dict'>":
                setattr(o, key, self._par(k[key]))
            else:
                setattr(o, key, k[key])
        return o


    def _dict_factory(self, cursor, row):
        """turn data into a dictionary"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


    def getPath(self, args, L=False):
        """Absolute path generation"""

        p = ""
        for val in args:
            p = os.path.join(p, val)
        return p


    def colorMsg(self, m="", c="red", flag=False):
        """Color text output"""
        colorSign = {
            "xx" : "\033[32m{0}\033[0m",
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


    def isIp(self, ipaddr, c = False):
        """ip match
            ipaddr : ip
            c : Dan IP number, default False
        """

        if not ipaddr:
            return False
        q = ipaddr.strip().split('.')
        l = 4 if c else len(q)
        qi = map(int, filter(lambda x: x.isdigit(), q))
        return len(q) == l and len(list(filter(lambda x: x >= 0 and x <= 255, qi))) == l


    def getArgs(self, args="", fs=","):
        """Processing parameters
            args : parameters
        """
        return args.rsplit(fs) if args else False


class TqdmBar(object):
    """文件传输进度条tqdm"""

    def __init__(self, t):
        self.t = t
        self.last_b = 0


    def progressBar(self, transferred, toBeTransferred, suffix=''):
        """tqdm进度条"""
        self.t.total = toBeTransferred
        self.t.update(transferred - self.last_b)
        self.last_b = transferred


def load_config():
    """get conf from config file"""
    cwd = os.path.dirname(os.path.realpath(sys.argv[0]))
    conf_name = "antshell.yml"
    conf_path = ["~/.antshell/", "/etc/antshell/", cwd]
    conf_path = list(map(lambda x:os.path.join(x, conf_name), conf_path))

    path0 = os.getenv("ANTSHELL_CONFIG", None)
    if path0 is not None:
        conf_path.insert(0, path0)

    for path in conf_path:
        path = os.path.expanduser(path)
        if os.path.exists(path) and os.path.isfile(path):
            try:
                conf = yaml.load(open(path))
                if not conf:
                    sys.exit()
                return conf
            except Exception as e:
                print(e)
                sys.exit()


def load_argParser():
    """command line parameter"""
    conf = load_config()
    langset = conf.get("langset", LANG.get("default"))
    lang = LANG[langset]
    usage = """%(prog)s [ -h | --version ] [-l [-m 2] ]
        [ v | -n 1 | -s 'ip|name' ] [ -G g1>g2 ]
        [ -e | -a ip [--name tag | --user root | --passwd xx | --port 22 ] | -d ip ]
        [ -P -c 'cmd1,cmd2,...' ]
        [ -f file_name [-g file_path | -p dir_path [-F ','] ] ]"""
    version = "%(prog)s " + __version__
    parser = argparse.ArgumentParser(
        prog = __prog__,
        usage = usage,
        description = lang["desc"],
        add_help = False)

    parser.add_argument("v", nargs="?", help="%s" %lang["v"])
    g1 = parser.add_argument_group("sys arguments")
    g1.add_argument("-h", "--help", action="help", help = lang["help"])
    g1.add_argument("--version", action = "version", version = version, help = lang["version"])
    g1.add_argument("--init", dest="init", action="store_true", default=False,
                        help=lang["init"])
    g1.add_argument("--update", dest="update", action="store_true", default=False,
                        help=lang["update"])

    g2 = parser.add_argument_group("edit arguments")
    g2.add_argument("-a", "--add", dest="add", action="store", type=str,
                        help=lang["add"], metavar="ip")
    g2.add_argument("-e", "--edit", dest="edit", action="store_true", default=False,
                        help=lang["edit"])
    g2.add_argument("-d", "--delete", dest="dels", action="store", type=str,
                        help=lang["delete"], metavar="ip")
    g2.add_argument("--name", dest="name", action="store", type=str,
                        help=lang["name"], metavar="tag")
    g2.add_argument("--user", dest="user", action="store", type=str,
                        help=lang["user"], metavar="root")
    g2.add_argument("--passwd", dest="passwd", action="store", type=str,
                        help=lang["passwd"], metavar="xxx")
    g2.add_argument("--port", dest="port", action="store", type=int,
                        help=lang["port"], metavar="22")

    g3 = parser.add_argument_group("host arguments")
    g3.add_argument("-l", dest="lists", action="store_true", default=False,
                        help=lang["lists"])
    g3.add_argument("-m", "--mode", dest="mode", action="store", type=int,
                        help=lang["mode"], default=0, metavar="2")
    g3.add_argument("-n", dest="num", action="store", type=int,
                        help=lang["num"], metavar=0)
    g3.add_argument("-s", "--search", dest="search", action="store", type=str,
                        help=lang["search"], metavar="'ip|name'")
    g3.add_argument("-G", dest="group", action="store", type=str,
                        help=lang["group"], metavar="g1>g2")

    g4 = parser.add_argument_group("manager arguments")
    g4.add_argument("-P", dest="para", action="store_true", default=False,
                        help=lang["para"])
    g4.add_argument("-c", dest="commod", action="store", type=str,
                        help=lang["commod"], metavar="'cmd1,cmd2,...'")
    g4.add_argument("-f", "--file", dest="file", action="store", type=str,
                        help=lang["file"], metavar="file_name")
    g4.add_argument("-g", "--get", dest="get", action="store", type=str,
                        help=lang["get"], metavar="file_path")
    g4.add_argument("-p", "--put", dest="put", action="store", type=str,
                        help=lang["put"], metavar="dir_path")
    g4.add_argument("-F", "--fs", dest="fs", action="store", type=str,
                        help=lang["fs"], default=",", metavar="','")
    return parser
