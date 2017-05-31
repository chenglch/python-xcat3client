# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from xcat3client.common import base


class NodeManager(base.Manager):
    _resource_name = 'nodes'

    def list(self):
        """Retrieve a list of nodes.
        :returns: A list of nodes.
        """
        url = self._resource_name
        return self._get(url)

    def post(self, body):
        url = self._resource_name
        return self._post(url, body)

    def show(self, node, fields=None):
        url = '%s/%s' % (self._resource_name, node)
        if fields:
            params = '&fields=' + ','.join(fields)
            url += '%s%s' % ('?', params)
        node = self._get(url, body=None)
        if node.get('osimage_id'):
            url = '%s/get_by_id?id=%s' % ('osimages', node['osimage_id'])
            osimage = self._get(url, body=None)
            node['osimage'] = osimage['name']
        return node

    def get(self, nodes, fields=None):
        url = '%s/%s' % (self._resource_name, 'info')
        if fields:
            params = '&fields=' + ','.join(fields)
            url += '%s%s' %('?', params)
        return self._get(url, body=nodes)

    def delete(self, nodes):
        url = self._resource_name
        return self._delete(url, body=nodes)

    def update(self, patch):
        url = '%s' % self._resource_name
        return self._update(url, patch=patch)

    def set_power_state(self, nodes, state):
        url = '%s/power?target=%s' % (self._resource_name, state)
        return self._put(url, body=nodes)

    def get_power_state(self, nodes):
        url = '%s/power' % (self._resource_name)
        return self._get(url, body=nodes)

    def set_provision_state(self, nodes, state, osimage, subnet):
        """Set the provision state for the nodes."""
        if not state:
            state = 'nodeset'
        url = "%s/provision?target=%s" % (self._resource_name, state)
        if osimage:
            url += '&osimage=%s' % osimage
        if subnet:
            url += '&subnet=%s' % subnet
        return self._put(url, body=nodes)

    def set_boot_device(self, nodes, boot_device):
        url = "%s/boot_device?target=%s" % (self._resource_name, boot_device)
        return self._put(url, body=nodes)

    def get_boot_device(self, nodes):
        url = "%s/boot_device" % (self._resource_name)
        return self._get(url, body=nodes)
