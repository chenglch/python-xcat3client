# Copyright 2013 Hewlett-Packard Development Company, L.P.
#    Updated 2017 for xcat purpose
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


class ServiceManager(base.ResourceManager):
    _resource_name = 'services'

    def get_by_hostname(self, hostname, fields=None):
        url = '%s/hostname?name=%s' % (self._resource_name, hostname)

        if fields:
            params = '&fields=' + ','.join(fields)
            url += params

        return self._get(url, body=None)

