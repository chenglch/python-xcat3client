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

from xcat3client.common import http
from xcat3client.v1 import node
from xcat3client.v1 import network
from xcat3client.v1 import nic
from xcat3client.v1 import osimage
from xcat3client.v1 import service
from xcat3client.v1 import passwd

class Client(object):
    """Client for the xCAT3 v1 API.

    :param string endpoint: A user-supplied endpoint URL for the xcat3
                            service.
    :param function token: Provides token for authentication.
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    """

    def __init__(self, *args, **kwargs):
        """Initialize a new client for the xCAT3 v1 API."""
        self.http_client = http._construct_http_client(*args, **kwargs)
        self.node = node.NodeManager(self.http_client)
        self.network = network.NetworkManager(self.http_client)
        self.nic = nic.NicManager(self.http_client)
        self.osimage = osimage.OSImageManager(self.http_client)
        self.service = service.ServiceManager(self.http_client)
        self.passwd = passwd.PasswdManager(self.http_client)
