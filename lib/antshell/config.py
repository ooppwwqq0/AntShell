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
from antshell.utils.errors import AntShellError
from antshell.utils.six import PY3
import os
import sys
import yaml
import shutil

if PY3:
    import configparser
else:
    import ConfigParser as configparser

INI_TYPE = "ini"
YAML_TYPE = "yaml"


class AntConfigParser(configparser.ConfigParser):
    def as_dict(self):
        '''将ini配置文件内容转化为字典'''
        d = dict(self._sections)
        for k in d:
            d[k] = dict(d[k])
        return d


def get_config_type(cfile):
    '''获取配置文件文件类型'''

    ftype = None
    if cfile is not None:
        ext = os.path.splitext(cfile)[-1]
        if ext in ('.ini', '.cfg'):
            ftype = INI_TYPE
        elif ext in ('.yaml', '.yml'):
            ftype = YAML_TYPE
    return ftype


def config_switch(config):
    '''
    将字典动态转换为类属性
    '''

    class o: 
        keys = []
        @classmethod
        def get_keys(cls):
            return cls.keys

    for key in config:
        o.keys.append(key.upper())
        if type(config[key]) == type(dict()):
            setattr(o, key.upper(), config_switch(config[key]))
        else:
            value = config[key]
            if config[key] == "True":
                value = True
            elif config[key] == "False":
                value = False
            setattr(o, key.upper(), value)
    return o


def find_config_file():
    '''
    获取所有配置文件路径
    '''

    cwd = os.path.dirname(os.path.realpath(sys.argv[0]))
    config_name = "antshell.cfg"
    base_path_list = ["~/.antshell/", "/etc/antshell/", cwd]

    custom_path = os.getenv("ANTSHELL_CONFIG", None)
    if custom_path is not None:
        if os.path.isdir(custom_path):
            base_path_list.insert(0, custom_path)

    config_path_list = list(map(lambda x: os.path.join(x, config_name), base_path_list))

    for config in config_path_list:
        config_path = os.path.expanduser(config)
        if config_path and os.path.exists(config_path) and os.path.isfile(config_path):
            break
    else:
        config_path = None
    return config_path


def load_config():
    '''
    加载配置文件
    '''
    
    config = None
    config_file = find_config_file()
    if config_file is None:
        raise AntShellError("can not find config file!")
    file_type = get_config_type(config_file)
    if file_type == INI_TYPE:
        try:
            conf = AntConfigParser()
            if PY3:
                conf.read(config_file, encoding="utf-8")
            else:
                conf.read(config_file)
            config = conf.as_dict()
        except Exception:
            raise AntShellError("load ini config file error!")
    elif file_type == YAML_TYPE:
        try:
            config = yaml.load(open(config_file))
        except Exception:
            raise AntShellError("load yaml config file error!")
    return config



def init_conf():
    '''
    初始化配置文件
    '''

    path = find_config_file()
    if not path:
        default_path= "~/.antshell"
        dpath = os.path.expanduser(default_path)
        if not os.path.exists(dpath):
            os.makedirs(dpath)
        config_name = "antshell.cfg"
        cwd = os.path.dirname(os.path.realpath(__file__))
        shutil.copy(os.path.join(cwd, "config/", config_name), os.path.join(dpath, config_name))

try:
    config = load_config()
    CONFIG = config_switch(config)
except AntShellError:
    print("Load Config Error, Auto Init Config!")
    init_conf()


if __name__ == "__main__":
    config = load_config()
    CONFIG = config_switch(config)
    print(CONFIG.get_keys())