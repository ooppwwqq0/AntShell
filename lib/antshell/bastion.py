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
from antshell.config import CONFIG
from antshell.utils.errors import DeBug
from antshell.base import BaseToolsBox
import os
import sys
import shutil
import time
import subprocess
import datetime

DEBUG = CONFIG.DEFAULT.DEBUG


def GetBastionConfig():
    '''
    获取堡垒机信息
    '''

    bastionInfo = {
        "host" : CONFIG.BASTION.BASTION_HOST,
        "port" : CONFIG.BASTION.BASTION_PORT,
        "user" : CONFIG.BASTION.BASTION_USER,
        "totp" : CONFIG.BASTION.BASTION_TOTP,
    }
    passwd = ""
    if CONFIG.BASTION.BASTION_TOTP:
        passwd = GetPasswdByTotp(CONFIG.BASTION.BASTION_TOTP)
    if passwd:
        passwd = CONFIG.BASTION.BASTION_PASSWD_PREFIX + passwd
    else:
        info = bastionInfo.get("user") + "@" + bastionInfo.get("host") + ":" + str(bastionInfo.get("port")) + "'s password: PIN:****** + Token:"
        passwd = CONFIG.BASTION.BASTION_PASSWD_PREFIX + str(input(info))
    bastionInfo["passwd"] = passwd

    DeBug(bastionInfo, DEBUG)
    return bastionInfo


def GetPasswdByTotp(totp):
    '''
    根据堡垒机totp获取动态密码
    '''
    
    try:
        passwd = subprocess.check_output(['oathtool', '-b', '--totp', totp, ]).rstrip(b'\n')
        return passwd.decode()
    except Exception:
        BaseToolsBox().colorMsg("Warning: oathtool is not exists!\nPlease execute 'brew install oath-toolkit' to install!\n")
        return False


if __name__ == "__main__":
    print(GetBastionConfig())