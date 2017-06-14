# Copyright 2012 Red Hat, Inc.
#
#    Updated 2017 for xcat test purpose
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# W0603: Using the global statement
# W0621: Redefining name %s from outer scope
# pylint: disable=W0603,W0621

from __future__ import print_function

import os
import json
import sys
import argparse
from xcat3client.common.i18n import _


class StoreDictKeyPair(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        my_dict = {}
        for kv in values.split(","):
            k, v = kv.split("=")
            my_dict[k] = v
        setattr(namespace, self.dest, my_dict)


class StoreDictKeyPairArray(argparse.Action):
    dict_list = []

    def __call__(self, parser, namespace, values, option_string=None):
        my_dict = {}
        for kv in values.split(","):
            k, v = kv.split("=")
            my_dict[k] = str2bool(v)
        self.dict_list.append(my_dict)
        setattr(namespace, self.dest, self.dict_list)


def str2bool(v):
    """Retruns bool if the value is bool format, otherwise retrun value"""
    if v.lower() in ("yes", "true", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "0", "n"):
        return False
    return v

def env(*args, **kwargs):
    """Returns the first environment variable set.

    If all are empty, defaults to '' or keyword arg `default`.
    """
    for arg in args:
        value = os.environ.get(arg)
        if value:
            return value
    return kwargs.get('default', '')


def arg(*args, **kwargs):
    """Decorator for CLI args.

    Example:

    >>> @arg("name", help="Name of the new entity")
    ... def entity_create(args):
    ...     pass
    """
    def _decorator(func):
        add_arg(func, *args, **kwargs)
        return func
    return _decorator


def add_arg(func, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""

    if not hasattr(func, 'arguments'):
        func.arguments = []

    # NOTE(sirp): avoid dups that can occur when the module is shared across
    # tests.
    if (args, kwargs) not in func.arguments:
        # Because of the semantics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.arguments.insert(0, (args, kwargs))


def print_list(objs, json_flag=False):
    """Print a list of objects or dict as a table, one row per object or dict.

    :param objs: iterable of :class:`Resource`
    :param json_flag: print the list as JSON instead of table
    """
    if json_flag:
        json.dumps(objs)
        return

    if not objs:
        print(_("Could not find any resource."))
    for item in objs:
        print(item)


def print_dict(dct):
    """Print a `dict` as a table of two columns.

    :param dct: `dict` to print
    """
    if not dct:
        print('Could not find any record')
        return

    print(json.dumps(dct,indent=4, sort_keys=False, ensure_ascii=False))


def service_type(stype):
    """Adds 'service_type' attribute to decorated function.

    Usage:

    .. code-block:: python

       @service_type('volume')
       def mymethod(f):
       ...
    """
    def inner(f):
        f.service_type = stype
        return f
    return inner


def get_service_type(f):
    """Retrieves service type from function."""
    return getattr(f, 'service_type', None)


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)


def exit(msg=''):
    if msg:
        print (msg, file=sys.stderr)
    sys.exit(1)
