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

VALID_FIELDS = ('ver', 'arch', 'distro', 'rootfstype')

@cliutils.arg(
    '--fields',
    metavar='<ver,arch,distro>',
    default=None,
    help="Fields seperated by comma. Only these fields will be fetched from "
         "the server.")
@cliutils.arg(
    'name',
    metavar='<name>',
    nargs=None,
    help="OSImage name to show")
def do_osimage_show(cc, args):
    """Show detailed information about osimage."""
    fields = []
    if args.fields:
        fields = args.fields.split(',')
    if fields and 'name' not in fields:
        fields.append('name')
    result = cc.osimage.show(args.name, fields)
    cliutils.print_dict(result)


def do_osimage_list(cc, args):
    """List the osimage(s) which are registered with the xCAT3 service."""
    osimages = cc.osimage.list()
    names = ['%s (osimage)' % osimage.get('name') for osimage in
             osimages['images']]
    cliutils.print_list(names, args.json)


@cliutils.arg('name',
              metavar='name',
              nargs=None,
              help="osimage name to delete")
def do_osimage_delete(cc, args):
    """Unregister osimage from xCAT3 service.

    :raises: ClientException, if error happens during the delete
    """
    cc.osimage.delete(args.name)
    print(_("%s deleted" % args.name))

@cliutils.arg(
    'name',
    nargs=None,
    metavar='<name>',
    help="OSImage name to update.")
@cliutils.arg(
    'attributes',
    metavar='<path=value>',
    nargs='+',
    action='append',
    default=[],
    help="Attribute to add, replace, or remove. Can be specified "
         "multiple times. if value is empty, remove operation will be taken."
         "Current valid fields %s" % ','.join(VALID_FIELDS))
def do_osimage_update(cc, args):
    """Update information about registered osimage."""

    patch = utils.args_array_to_patch(args.attributes[0])
    result = cc.osimage.update(args.name, patch)
    cliutils.print_dict(result)
