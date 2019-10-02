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
import types

_BUNDLED_METADATA = {"pypi_name": "six", "version": "1.11.0"}

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PY34 = sys.version_info[0:2] >= (3, 4)

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes

    MAXSIZE = sys.maxsize
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

    if sys.platform.startswith("java"):
        # Jython always uses 32 bits.
        MAXSIZE = int((1 << 31) - 1)
    else:
        # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
        class X(object):

            def __len__(self):
                return 1 << 31
        try:
            len(X())
        except OverflowError:
            # 32-bit
            MAXSIZE = int((1 << 31) - 1)
        else:
            # 64-bit
            MAXSIZE = int((1 << 63) - 1)
        del X



def _import_module(name):
    """Import module, returning the module after the last dot."""
    __import__(name)
    return sys.modules[name]


# class _LazyDescr(object):

#     def __init__(self, name):
#         self.name = name

#     def __get__(self, obj, tp):
#         result = self._resolve()
#         setattr(obj, self.name, result)  # Invokes __set__.
#         try:
#             # This is a bit ugly, but it avoids running this again by
#             # removing this descriptor.
#             delattr(obj.__class__, self.name)
#         except AttributeError:
#             pass
#         return result


# class MovedModule(_LazyDescr):

#     def __init__(self, name, old, new=None):
#         super(MovedModule, self).__init__(name)
#         if PY3:
#             if new is None:
#                 new = name
#             self.mod = new
#         else:
#             self.mod = old

#     def _resolve(self):
#         return _import_module(self.mod)

#     def __getattr__(self, attr):
#         _module = self._resolve()
#         value = getattr(_module, attr)
#         setattr(self, attr, value)
#         return value


# _moved_attributes = [
#     MovedModule("configparser", "ConfigParser"),
# ]