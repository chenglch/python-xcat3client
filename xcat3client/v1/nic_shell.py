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


VALID_FIELDS = ('uuid','mac', 'name', 'ip', 'netmask', 'extra', 'node')
REQUIRE_FIELDS = ('mac', 'node')

def _validate(attr_dict):
    for attr in REQUIRE_FIELDS:
        if not attr_dict.has_key(attr):
            print(_('Could not find required field %(attr)s' % {'attr':attr}))
            exit(1)

@cliutils.arg(
    '--mac',
    metavar='<mac address>',
    default=None,
    help="Search nic by mac address")
@cliutils.arg(
    '--fields',
    metavar='<mac,ip,netmask,node>',
    default=None,
    help="Fields seperated by comma. Only these fields will be fetched from "
         "the server.")
@cliutils.arg(
    'uuid',
    metavar='<uuid>',
    nargs='?',
    help="Nic uuid to show")
def do_nic_show(cc, args):
    """Show detailed infomation about nic."""
    fields = []
    if args.fields:
        fields = args.fields.split(',')
    if fields and 'uuid' not in fields:
        fields.append('uuid')
    if args.uuid:
        result = cc.nic.show(args.uuid, fields)
    elif args.mac:
        result = cc.nic.get_by_mac(args.mac)
    else:
        print (_("Invalid argument given."))
        return
    cliutils.print_dict(result)


def do_nic_list(cc, args):
    """List the nic(s) which are registered with the xCAT3 service."""
    nics = cc.nic.list()
    names = ['%s (uuid) %s (mac)' % (nic.get('uuid'), nic.get('mac')) for nic in
             nics['nics']]
    cliutils.print_list(names, args.json)


@cliutils.arg(
    'attributes',
    metavar='<path=value>',
    nargs='+',
    action='append',
    default=[],
    help="Attribute to add, replace, or remove. Can be specified "
         "multiple times. Current valid fields %s" % ','.join(VALID_FIELDS))
def do_nic_create(cc, args):
    """Register nic into xCAT3 service."""
    dct = utils.to_attrs_dict(args.attributes[0], VALID_FIELDS)
    _validate(dct)
    result = cc.nic.post(dct)
    cliutils.print_dict(result)


@cliutils.arg('uuid',
              metavar='uuid',
              nargs=None,
              help="nic uuid to delete")
def do_nic_delete(cc, args):
    """Unregister nic from xCAT3 service.

    :raises: ClientException, if error happens during the delete
    """
    cc.nic.delete(args.uuid)
    print(_("%s deleted" % args.uuid))

@cliutils.arg(
    'uuid',
    nargs=None,
    metavar='<uuid>',
    help="Nic uuid to update.")
@cliutils.arg(
    'attributes',
    metavar='<path=value>',
    nargs='+',
    action='append',
    default=[],
    help="Attribute to add, replace, or remove. Can be specified "
         "multiple times. if value is empty, remove operation will be taken."
         "Current valid fields %s" % ','.join(VALID_FIELDS))
def do_nic_update(cc, args):
    """Update information about registered nic(s)."""

    patch = utils.args_array_to_patch(args.attributes[0])
    result = cc.nic.update(args.uuid, patch)
    cliutils.print_dict(result)
