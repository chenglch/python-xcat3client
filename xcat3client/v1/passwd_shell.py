# Copyright 2013 Red Hat, Inc.
# 2017 for xcat test purpose.
# All Rights Reserved.
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

from xcat3client.common import cliutils
from xcat3client.common.i18n import _
from xcat3client.common import utils

VALID_FIELDS = ('username', 'password', 'crypt_method')

@cliutils.arg(
    '--fields',
    metavar='<userkey,password,crypt_method>',
    default=None,
    help="Fields seperated by comma. Only these fields will be fetched from "
         "the server.")
@cliutils.arg(
    'key',
    metavar='<key>',
    nargs=None,
    help="Passwd key to show")
def do_passwd_show(cc, args):
    """Show detailed information about passwd."""
    fields = []
    if args.fields:
        fields = args.fields.split(',')
    if fields and 'key' not in fields:
        fields.append('key')
    result = cc.passwd.show(args.key, fields)
    cliutils.print_dict(result)


def do_passwd_list(cc, args):
    """List the passwd(s) which are registered with the xCAT3 service."""
    passwds = cc.passwd.list()
    passwds = ['%s (passwd)' % passwd.get('key') for passwd in
             passwds['passwds']]
    cliutils.print_list(passwds, args.json)


@cliutils.arg('key',
              metavar='key',
              nargs=None,
              help="passwd key to delete")
def do_passwd_delete(cc, args):
    """Unregister passwd from xCAT3 service.

    :raises: ClientException, if error happens during the delete
    """
    cc.passwd.delete(args.key)
    print(_("%s deleted" % args.key))

@cliutils.arg(
    'key',
    nargs=None,
    metavar='<key>',
    help="OSImage key to update.")
@cliutils.arg(
    'attributes',
    metavar='<path=value>',
    nargs='+',
    action='append',
    default=[],
    help="Attribute to add, replace, or remove. Can be specified "
         "multiple times. if value is empty, remove operation will be taken."
         "Current valid fields %s" % ','.join(VALID_FIELDS))
def do_passwd_update(cc, args):
    """Update information about registered passwd."""

    patch = utils.args_array_to_patch(args.attributes[0])
    result = cc.passwd.update(args.key, patch)
    cliutils.print_dict(result)


@cliutils.arg(
    'key',
    nargs=None,
    metavar='<key>',
    help="passwd key to create")
@cliutils.arg(
    'attributes',
    metavar='<path=value>',
    nargs='+',
    action='append',
    default=[],
    help="Attribute to add, replace, or remove. Can be specified "
         "multiple times. Current valid fields %s" % ','.join(VALID_FIELDS))
def do_passwd_create(cc, args):
    """Register passwd into xCAT3 service."""
    dct = utils.to_attrs_dict(args.attributes[0], VALID_FIELDS)
    dct['key'] = args.key
    result = cc.passwd.post(dct)
    cliutils.print_dict(result)