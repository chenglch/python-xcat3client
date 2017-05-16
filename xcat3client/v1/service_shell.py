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
from xcat3client import exc



@cliutils.arg(
    'hostname',
    metavar='<hostname>',
    nargs=None,
    help="Service hostname to show")
def do_service_show(cc, args):
    """Show detailed information about service."""
    result = cc.service.get_by_hostname(args.hostname)
    cliutils.print_dict(result)


def do_service_list(cc, args):
    """List the service(s) which are registered with the xCAT3 service."""
    services = cc.service.list()
    messages = []
    for service in services['services']:
        name = service.get('hostname')
        online = 'online' if service.get('online') else 'offline'
        message = '%(name)s(%(type)s): %(online)s' % {
            'name': name, 'type': service.get('type'), 'online': online}
        if service.get('online'):
            message += ' workers: %s' % service.get('workers')
        messages.append(message)
    cliutils.print_list(messages, args.json)
