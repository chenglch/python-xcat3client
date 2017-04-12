# Copyright 2012 OpenStack LLC.
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

"""
Base utilities to build API operation managers and objects on top of.
"""

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class Manager(object):
    """Provides  CRUD operations with a particular API."""

    def __init__(self, api):
        self.api = api

    def _get(self, url, body=None):
        """Retrieve a resource."""
        return self.api.get(url, body=body)[1]


    def _post(self, url, body):
        return self.api.post(url, body=body)[1]

    def _update(self, url, patch):
        """Update a resource.

        :param url: Resource identifier.
        :param patch: New version of a given resource.
        """
        return self.api.patch(url, body=patch)[1]

    def _put(self, url, body):
        return self.api.put(url, body=body)[1]

    def _delete(self, url, body=None):
        """Delete a resource.

        :param resource_id: Resource identifier.
        """
        return self.api.delete(url, body=body)[1]


@six.add_metaclass(abc.ABCMeta)
class ResourceManager(Manager):

    def list(self):
        """Retrieve a list of networks.
        :returns: A list of networks.
        """
        url = self._resource_name
        return self._get(url)

    def post(self, body):
        url = self._resource_name
        return self._post(url, body)

    def show(self, name, fields=None):
        url = '%s/%s' % (self._resource_name, name)
        if fields:
            params = '&fields=' + ','.join(fields)
            url += '%s%s' % ('?', params)
        return self._get(url, body=None)

    def delete(self, name):
        url = '%s/%s' % (self._resource_name, name)
        return self._delete(url)

    def update(self, name, patch):
        url = '%s/%s' % (self._resource_name, name)
        return self._update(url, patch=patch)
