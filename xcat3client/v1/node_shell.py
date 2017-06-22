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
import sys

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

    if success != total:
        sys.exit(1)


def _parallel_create(func, nodes, total, split_num):
    import eventlet
    eventlet.monkey_patch(os=False)
    import futurist
    from futurist import waiters
    data = []
    i = 0
    per_split = total / split_num
    while i < split_num - 1:
        data.append({'nodes': nodes[i * per_split:(i + 1) * per_split]})
        i += 1
    data.append({'nodes': nodes[i * per_split:]})
    _executor = futurist.GreenThreadPoolExecutor(max_workers=split_num)
    j = 0
    futures = []
    while j < split_num:
        future = _executor.submit(func, data[j])
        futures.append(future)
        j += 1

    done, not_done = waiters.wait_for_all(futures, 3600)
    result = {'nodes': {}}
    for r in done:
        result['nodes'].update(r.result()['nodes'])

    return result


def _parallel_update(func, names, patch, total, split_num):
    import eventlet
    eventlet.monkey_patch(os=False)
    import futurist
    from futurist import waiters
    patch_dicts = []
    patch_dict = {'nodes': [], "patches": patch}
    i = 0
    per_split = total / split_num
    while i < total:
        if i != 0 and i % per_split == 0 and i != split_num * per_split:
            patch_dicts.append(patch_dict)
            patch_dict = {'nodes': [], "patches": patch}

        patch_dict['nodes'].append({'name': names[i]})
        i += 1
    patch_dicts.append(patch_dict)

    _executor = futurist.GreenThreadPoolExecutor(max_workers=split_num)
    futures = []
    for patch_dict in patch_dicts:
        future = _executor.submit(func, patch_dict)
        futures.append(future)

    done, not_done = waiters.wait_for_all(futures, 3600)
    result = {'nodes': {}}
    for r in done:
        result['nodes'].update(r.result()['nodes'])

    return result


@cliutils.arg(
    '-i, --fields',
    dest='fields',
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
    if 'nics' in fields:
        fields.remove('nics')
        fields.append('nics_info')
    if 'control' in fields:
        fields.remove('control')
        fields.append('control_info')

    if len(nodes) == 1:
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
    fields = ['name', 'mgt', 'netboot', 'type', 'arch', 'nics_info',
              'control_info']
    result = cc.node.get(node_dict, fields)
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
    if i > 3000:
        result = _parallel_create(cc.node.post, nodes, i, 4)
    else:
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
    'attributes',
    metavar='<path=value>',
    nargs='+',
    action='append',
    default=[],
    help="Attribute to add, Current support arch, netboot, mgt")
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
    attr_dict = {}
    names = _get_node_from_args(args.nodes)
    for attr in args.attributes[0]:
        key, value = utils.split_and_deserialize(attr)
        if key not in fields:
            raise exc.BadRequest('Can not support attribute %s' % key)
        attr_dict[key] = value

    for name in names:
        node = dict((k, v) for k, v in six.iteritems(attr_dict))
        node['name'] = name
        node['control_info'] = args.control
        if args.nic:
            node['nics_info'] = {'nics': args.nic}
        nodes['nodes'].append(node)

    count = len(nodes['nodes'])
    if count > 3000:
        result = _parallel_create(cc.node.post, nodes['nodes'], count, 4)
    else:
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
    count = len(names)
    if count > 3000:
        result = _parallel_update(cc.node.update, names, patch, count, 4)
    else:
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
    choices=['on', 'off', 'boot', 'status'],
    help="'on', 'off', 'status' or 'boot'.")
def do_power(cc, args):
    """Power operation on/off/reset/status for nodes"""
    names = _get_node_from_args(args.nodes)
    nodes = {'nodes': []}
    map(lambda x: nodes['nodes'].append({'name': x}), names)
    if args.power_state == 'status':
        result = cc.node.get_power_state(nodes)
    else:
        result = cc.node.set_power_state(nodes, args.power_state)
    _print_node_result(result, args, True)


@cliutils.arg(
    'nodes',
    nargs=None,
    metavar='<nodes>',
    help="Multiple node names split by comma.")
@cliutils.arg(
    'boot_device',
    metavar='<boot-device>',
    choices=['net', 'disk', 'status', 'cdrom'],
    help="'net', 'disk', 'status' or 'cdrom'.")
def do_bootdev(cc, args):
    """Set/Get next boot device (net or disk or cdrom)."""
    names = _get_node_from_args(args.nodes)
    nodes = {'nodes': []}
    map(lambda x: nodes['nodes'].append({'name': x}), names)
    if args.boot_device == 'status':
        result = cc.node.get_boot_device(nodes)
    else:
        result = cc.node.set_boot_device(nodes, args.boot_device)
    _print_node_result(result, args, True)


@cliutils.arg(
    'nodes',
    nargs=None,
    metavar='<nodes>',
    help="Multiple node names split by comma.")
@cliutils.arg(
    '--state',
    metavar='<state>',
    choices=['nodeset', 'dhcp'],
    nargs='?',
    default='nodeset',
    help="'nodeset' or 'dhcp'.")
@cliutils.arg(
    '--osimage',
    metavar='<osimage>',
    default=None,
    help='osimage to setup')
@cliutils.arg(
    '--network',
    metavar='<network>',
    default=None,
    help='network for node provision')
@cliutils.arg(
    '-d, --delete',
    action='store_true',
    dest='delete',
    default=False,
    help='Clean up related state, like un_dhcp, un_nodeset')
def do_deploy(cc, args):
    """Deployment service for nodes (not complete)"""
    names = _get_node_from_args(args.nodes)
    nodes = {'nodes': []}
    map(lambda x: nodes['nodes'].append({'name': x}), names)
    state = args.state
    if args.delete:
        state = 'un_%s' % state
    result = cc.node.set_provision_state(nodes, state, args.osimage,
                                         args.network)
    _print_node_result(result, args, True)
