# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#    Updated 2017 for xcat test purpose
#
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

from __future__ import print_function

import argparse
import contextlib
import json
import shutil
import tempfile
import time

from oslo_utils import importutils

from xcat3client.common.i18n import _
from xcat3client import exc


class HelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(HelpFormatter, self).start_section(heading)


def define_command(subparsers, command, callback, cmd_mapper):
    '''Define a command in the subparsers collection.

    :param subparsers: subparsers collection where the command will go
    :param command: command name
    :param callback: function that will be used to process the command
    '''
    desc = callback.__doc__ or ''
    help = desc.strip().split('\n')[0]
    arguments = getattr(callback, 'arguments', [])

    subparser = subparsers.add_parser(command, help=help,
                                      description=desc,
                                      add_help=False,
                                      formatter_class=HelpFormatter)
    subparser.add_argument('-h', '--help', action='help',
                           help=argparse.SUPPRESS)
    cmd_mapper[command] = subparser
    for (args, kwargs) in arguments:
        subparser.add_argument(*args, **kwargs)
    subparser.set_defaults(func=callback)


def define_commands_from_module(subparsers, command_module, cmd_mapper):
    """Add *do_* methods in a module and add as commands into a subparsers."""

    for method_name in (a for a in dir(command_module) if a.startswith('do_')):
        # Commands should be hypen-separated instead of underscores.
        command = method_name[3:].replace('_', '-')
        callback = getattr(command_module, method_name)
        define_command(subparsers, command, callback, cmd_mapper)


def import_versioned_module(version, submodule=None):
    module = 'xcat3client.v%s' % version
    if submodule:
        module = '.'.join((module, submodule))
    return importutils.import_module(module)


def split_and_deserialize(string):
    """Split and try to JSON deserialize a string.

    Gets a string with the KEY=VALUE format, split it (using '=' as the
    separator) and try to JSON deserialize the VALUE.

    :returns: A tuple of (key, value).
    """
    try:
        key, value = string.split("=", 1)
    except ValueError:
        raise exc.CommandError(_('Attributes must be a list of '
                                 'PATH=VALUE not "%s"') % string)
    try:
        value = json.loads(value)
    except ValueError:
        pass

    return (key, value)


def args_array_to_dict(kwargs, key_to_convert):
    values_to_convert = kwargs.get(key_to_convert)
    if values_to_convert:
        kwargs[key_to_convert] = dict(split_and_deserialize(v)
                                      for v in values_to_convert)
    return kwargs


def args_array_to_patch(attributes):
    patch = []
    for attr in attributes:
        # Sanitize
        if not attr.startswith('/'):
            attr = '/' + attr

        path, value = split_and_deserialize(attr)
        if value:
            patch.append({'op': 'add', 'path': path, 'value': value})
        else:
            # NOTE(chenglch): If no value is given, it means remove current
            # attribute if exist
            patch.append({'op': 'remove', 'path': path})
    return patch


@contextlib.contextmanager
def tempdir(*args, **kwargs):
    dirname = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield dirname
    finally:
        shutil.rmtree(dirname)


def check_empty_arg(arg, arg_descriptor):
    if not arg.strip():
        raise exc.CommandError(_('%(arg)s cannot be empty or only have blank'
                                 ' spaces') % {'arg': arg_descriptor})


@contextlib.contextmanager
def record_time(times, enabled, *args):
    """Record the time of a specific action.

    :param times: A list of tuples holds time data.
    :type times: list
    :param enabled: Whether timing is enabled.
    :type enabled: bool
    :param *args: Other data to be stored besides time data, these args
                  will be joined to a string.
    """
    if not enabled:
        yield
    else:
        start = time.time()
        yield
        end = time.time()
        times.append((' '.join(args), start, end))


def write_to_file(path, contents):
    with open(path, 'w') as f:
        f.write(contents)


def to_attrs_dict(attrs, VALID_FIELDS):
    dct = {}
    for attr in attrs:
        k, v = attr.split('=')
        if k not in VALID_FIELDS:
            print(_('Unsupport attrbute %s '), k)
            exit(1)
        dct[k] = v
    return dct
