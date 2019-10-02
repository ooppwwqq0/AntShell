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
import sys
__metaclass__ = type


class AntShellError(Exception):
    '''
    打印错误信息
    '''

    def __init__(self, message="", obj=None, show_content=True, suppress_extended_error=False, orig_exc=None):
        super(AntShellError, self).__init__(message)
        self.message = message

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message

class DeBug(object):
    '''
    打印debug信息
    '''

    def __init__(self, message="", debug=False):
        self.debug = debug
        self.message = message
        self.print_message()
    
    def __str__(self):
        return self.message
    
    def __repr__(self):
        return self.message
    
    def print_message(self):
        if self.debug:
            print(self.message)
