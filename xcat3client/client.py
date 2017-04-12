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

from xcat3client.common import utils


def get_client(xcat3_url=None, insecure=None, timeout=None,
               os_cacert=None, ca_file=None, os_cert=None, cert_file=None,
               os_key=None, key_file=None, max_retries=None,
               retry_interval=None, **ignored_kwargs):
    """Get an authenticated client, based on the credentials.

    :param xcat3_url: xcat3 API endpoint
    :param insecure: allow insecure SSL (no cert verification)
    :param timeout: allows customization of the timeout for client HTTP
        requests
    :param os_cacert: path to cacert file
    :param ca_file: path to cacert file, deprecated in favour of os_cacert
    :param os_cert: path to cert file
    :param cert_file: path to cert file, deprecated in favour of os_cert
    :param os_key: path to key file
    :param key_file: path to key file, deprecated in favour of os_key
    :param max_retries: Maximum number of retries in case of conflict error
    :param retry_interval: Amount of time (in seconds) between retries in case
        of conflict error
    :param ignored_kwargs: all the other params that are passed. Left for
        backwards compatibility. They are ignored.
    """
    version = '1'
    kwargs = {
        'max_retries': max_retries,
        'retry_interval': retry_interval,
    }
    endpoint = xcat3_url
    cacert = os_cacert or ca_file
    cert = os_cert or cert_file
    key = os_key or key_file
    if endpoint:
        kwargs.update({
            'insecure': insecure,
            'ca_file': cacert,
            'cert_file': cert,
            'key_file': key,
            'timeout': timeout,
        })

    return Client(version, endpoint, **kwargs)


def Client(version, *args, **kwargs):
    module = utils.import_versioned_module(version, 'client')
    client_class = getattr(module, 'Client')
    return client_class(*args, **kwargs)
