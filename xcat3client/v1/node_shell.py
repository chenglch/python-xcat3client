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

import json
import six

from xcat3client.common import cliutils
from xcat3client.common.i18n import _
from xcat3client.common import utils
from xcat3client import exc

FIELD_DICT = {'control': 'control_info',
              'nics': 'nics_info'}
SUCCESS_RESULTS = {'ok': True,
                   'updated': True,
                   'deleted': True,
                   'on': True,
                   'off': True,
                   'net': True,
                   'cdrom': True,
                   'disk': True,
                   'provision': True}


def _get_node_from_args(nodes=None):
    """Build the node(s) from node range"""
    name_list = []
    if nodes:
        nodes = nodes.split(',')
    for node in nodes:
        names = []
        try:
            if '[' in node and '-' in node and ']' in node:
                parts = node.split('[')
                prefix = parts[0]
                num_parts = parts[1].split('-')
                left = int(num_parts[0])
                right = int(num_parts[1].split(']')[0])

                while (left <= right):
                    name = "%s%d" % (prefix, left)
                    names.append(name)
                    left += 1
            else:
                node = node.replace('[', '').replace(']', '')
                names.append(node)
            name_list.extend(names)
        except Exception() as e:
            err = _("Invalied node name %(name)s. Error: %(err)s")
            raise exc.InvalidName(err % {'name': node, 'err': e})

    return list(set(name_list))


def _print_node_result(result, args, check=False):
    """Help function to calculate the success results then print"""
    success = 0
    total = 0
    rst = []
    for k, v in six.iteritems(result['nodes']):
        if check and SUCCESS_RESULTS.has_key(v):
            success += 1
        total += 1
        rst.append(k + ': ' + v)
    cliutils.print_list(rst, args.json)
    if check:
        print('\nSuccess: %d  Total: %d' % (success, total))
    else:
        print('\nTotal: %d' % (total))


@cliutils.arg(
    '--fields',
    metavar='<mgt,name,nics>',
    default=None,
    help="Fields seperated by comma. Only these fields will be fetched from "
         "the server.")
@cliutils.arg(
    'nodes',
    metavar='<name>',
    nargs=None,
    help="Multiple node names split by comma.")
def do_show(cc, args):
    """Show detailed information about node(s)."""

    def format(result):
        out = []
        if result.has_key('nodes'):
            result = result.get('nodes')
            for r in result:
                node = dict()
                node['node'] = r.get('name')
                node['attr'] = r
                out.append(node)
        else:
            node = dict()
            node['node'] = result.get('name')
            node['attr'] = result
            out.append(node)
        return out

    nodes = _get_node_from_args(args.nodes)
    fields = []
    if args.fields:
        fields = args.fields.split(',')
    if fields and 'name' not in fields:
        fields.append('name')
    if len(nodes) == 1:
        if 'nics' in fields:
            fields.remove('nics')
            fields.append('nics_info')
        result = cc.node.show(nodes[0], fields)
        result = format(result)
        cliutils.print_dict(result)
        return

    node_dict = {'nodes': []}
    map(lambda x: node_dict['nodes'].append({'name': x}), nodes)
    result = cc.node.get(node_dict, fields)
    result = format(result)
    cliutils.print_dict(result)


@cliutils.arg(
    '-o', '--output',
    metavar='</tmp/data.json>',
    default=None,
    help="The output file stores nodes data.")
@cliutils.arg(
    'nodes',
    metavar='<name>',
    nargs=None,
    help="Multiple node names split by comma.")
def do_export(cc, args):
    """Export node(s) information as a specific json data file"""
    nodes = _get_node_from_args(args.nodes)
    node_dict = {'nodes': []}
    map(lambda x: node_dict['nodes'].append({'name': x}), nodes)
    result = cc.node.get(node_dict)
    utils.write_to_file(args.output, json.dumps(result))
    print(_("Export nodes data succefully."))


@cliutils.arg(
    'input',
    metavar='</tmp/data.json>',
    default=None,
    help="The input file stores nodes data.")
def do_import(cc, args):
    """Import node(s) information from json data file"""
    with open(args.input, 'r') as f:
        data = json.load(f)
    nodes = data['nodes']
    i = 0
    while i < len(nodes):
        nodes[i] = dict((k, v) for k, v in six.iteritems(nodes[i]) if v)
        i += 1
    result = cc.node.post(data)
    _print_node_result(result, args, True)


@cliutils.arg(
    'nodes',
    metavar='<nodes>',
    nargs='?',
    help="Multiple node names split by comma.")
def do_list(cc, args):
    """List the node(s) which are registered with the xCAT3 service."""
    targets = _get_node_from_args(args.nodes) if args.nodes else []
    nodes = cc.node.list()
    if targets:
        dct = dict((x, True) for x in targets)
        names = [node + ' (node)' for node in nodes['nodes'] if
                 dct.get(node)]
    else:
        names = [node + ' (node)' for node in nodes['nodes']]
    cliutils.print_list(names, args.json)


@cliutils.arg(
    'nodes',
    metavar='<nodes>',
    nargs=None,
    help="Multiple node names split by comma.")
@cliutils.arg(
    '--mgt',
    metavar='<mgt>',
    default=None,
    help='management technique')
@cliutils.arg(
    '--netboot',
    metavar='<netboot>',
    default=None,
    help='Netboot method, like pxe, petitboot, grub, yaboot etc.')
@cliutils.arg(
    '--arch',
    metavar='<arch>',
    default=None,
    help='Architecture of machine, like x86_64, ppc64le, ppc64')
@cliutils.arg(
    '-c', '--control',
    metavar='<key=value>[,<key=val>]',
    default=None,
    action=cliutils.StoreDictKeyPair,
    help='Key/value pairs split by comma used by the control plugin, such as '
         'bmc_address=11.0.0.0,bmc_password=password,bmc_username=admin')
@cliutils.arg(
    '-i', '--nic',
    metavar='<key=value>[,<key=value>]',
    action=cliutils.StoreDictKeyPairArray,
    default=None,
    help='Key/value pairs split by comma to indicate network information, '
         'like: '
         '-i mac=42:87:0a:05:00:00,primary=True,name=eth0 '
         '-i mac=42:87:0a:05:00:00,name=eth1')
def do_create(cc, args):
    """Enroll node(s) into xCAT3 service"""
    nodes = {'nodes': []}
    fields = ('arch', 'netboot', 'mgt', 'type')
    names = _get_node_from_args(args.nodes)

    for name in names:
        node = dict((k, getattr(args, k)) for k in fields if hasattr(args, k))
        node['name'] = name
        node['control_info'] = args.control
        if args.nic:
            node['nics_info'] = {'nics': args.nic}
        nodes['nodes'].append(node)
    result = cc.node.post(nodes)
    _print_node_result(result, args, True)


@cliutils.arg('nodes',
              metavar='<nodes>',
              nargs=None,
              help="Multiple node names split by comma.")
def do_delete(cc, args):
    """Unregister node(s) from the xCAT3 service.

    :raises: ClientException, if error happens during the delete
    """
    names = _get_node_from_args(args.nodes)
    nodes = {'nodes': []}
    map(lambda x: nodes['nodes'].append({'name': x}), names)
    result = cc.node.delete(nodes)
    _print_node_result(result, args, True)


@cliutils.arg(
    'nodes',
    nargs=None,
    metavar='<nodes>',
    help="Multiple node names split by comma.")
@cliutils.arg(
    'attributes',
    metavar='<path=value>',
    nargs='+',
    action='append',
    default=[],
    help="Attribute to add, replace, or remove. Can be specified "
         "multiple times. if value is empty, remove operation will be taken.")
def do_update(cc, args):
    """Update information about registered node(s)."""

    names = _get_node_from_args(args.nodes)
    patch = utils.args_array_to_patch(args.attributes[0])
    # NOTE(chenglch): makes argument prefix shorter
    for p in patch:
        key = p['path'].split('/')[1]
        if FIELD_DICT.has_key(key):
            p['path'] = p['path'].replace(key, FIELD_DICT[key])
    patch_dict = {'nodes': [], "patches": patch}
    map(lambda x: patch_dict['nodes'].append({'name': x}), names)
    result = cc.node.update(patch_dict)
    _print_node_result(result, args, True)


@cliutils.arg(
    'nodes',
    nargs=None,
    metavar='<nodes>',
    help="Multiple node names split by comma.")
@cliutils.arg(
    'power_state',
    metavar='<power-state>',
    choices=['on', 'off', 'reboot'],
    help="'on', 'off', or 'reboot'.")
def do_set_power(cc, args):
    """Power nodes on or off or reboot."""
    names = _get_node_from_args(args.nodes)
    nodes = {'nodes': []}
    map(lambda x: nodes['nodes'].append({'name': x}), names)
    result = cc.node.set_power_state(nodes, args.power_state)
    _print_node_result(result, args, True)


@cliutils.arg(
    'nodes',
    nargs=None,
    metavar='<nodes>',
    help="Multiple node names split by comma.")
def do_get_power(cc, args):
    """Get power state of nodes."""
    names = _get_node_from_args(args.nodes)
    nodes = {'nodes': []}
    map(lambda x: nodes['nodes'].append({'name': x}), names)
    result = cc.node.get_power_state(nodes)
    _print_node_result(result, args, True)


@cliutils.arg(
    'nodes',
    nargs=None,
    metavar='<nodes>',
    help="Multiple node names split by comma.")
def do_get_boot_device(cc, args):
    """Get next boot device of nodes."""
    names = _get_node_from_args(args.nodes)
    nodes = {'nodes': []}
    map(lambda x: nodes['nodes'].append({'name': x}), names)
    result = cc.node.get_boot_device(nodes)
    _print_node_result(result, args, True)


@cliutils.arg(
    'nodes',
    nargs=None,
    metavar='<nodes>',
    help="Multiple node names split by comma.")
@cliutils.arg(
    'boot_device',
    metavar='<boot-device>',
    choices=['net', 'disk', 'cdrom'],
    help="'net', 'disk', or 'cdrom'.")
def do_set_boot_device(cc, args):
    """Set next boot device net or disk or cdrom."""
    names = _get_node_from_args(args.nodes)
    nodes = {'nodes': []}
    map(lambda x: nodes['nodes'].append({'name': x}), names)
    result = cc.node.set_boot_device(nodes, args.boot_device)
    _print_node_result(result, args, True)


@cliutils.arg(
    'nodes',
    nargs=None,
    metavar='<nodes>',
    help="Multiple node names split by comma.")
@cliutils.arg(
    'target',
    metavar='<target>',
    choices=['diskfull', 'diskless', 'dhcp', 'hosts'],
    help="'diskfull', 'diskless', or 'dhcp'.")
def do_set_provision(cc, args):
    """Deployment service for nodes (not complete)"""
    names = _get_node_from_args(args.nodes)
    nodes = {'nodes': []}
    map(lambda x: nodes['nodes'].append({'name': x}), names)
    result = cc.node.set_provision_state(nodes, args.target)
    _print_node_result(result, args, True)
