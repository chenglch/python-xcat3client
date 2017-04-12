# Copyright 2012 OpenStack LLC.
# 2017 for xcat test purpose
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

import copy
import functools
import json
import logging
import time
import requests
import six.moves.urllib.parse as urlparse

from xcat3client.common.apiclient import exception
from xcat3client.common import utils
from xcat3client.common.i18n import _LE
from xcat3client import exc

LOG = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_INTERVAL = 2
SUPPORTED_ENDPOINT_SCHEME = ('http', 'https')
API_VERSION = '/v1'


def _trim_endpoint_api_version(url):
    """Trim API version and trailing slash from endpoint."""
    return url.rstrip('/').rstrip(API_VERSION)


def _extract_error_json(body):
    """Return  error_message from the HTTP response body."""
    error_json = {}
    try:
        body_json = json.loads(body)
        if 'error_message' in body_json:
            raw_msg = body_json['error_message']
            error_json = json.loads(raw_msg)
    except ValueError:
        pass

    return error_json


def get_server(endpoint):
    """Extract and return the server & port that we're connecting to."""
    if endpoint is None:
        return None, None
    parts = urlparse.urlparse(endpoint)
    return parts.hostname, str(parts.port)


_RETRY_EXCEPTIONS = (exc.Conflict, exc.ServiceUnavailable,
                     exc.ConnectionRefused)


def with_retries(func):
    """Wrapper for _http_request adding support for retries."""

    @functools.wraps(func)
    def wrapper(self, url, method, **kwargs):
        if self.conflict_max_retries is None:
            self.conflict_max_retries = DEFAULT_MAX_RETRIES
        if self.conflict_retry_interval is None:
            self.conflict_retry_interval = DEFAULT_RETRY_INTERVAL

        num_attempts = self.conflict_max_retries + 1
        for attempt in range(1, num_attempts + 1):
            try:
                return func(self, url, method, **kwargs)
            except _RETRY_EXCEPTIONS as error:
                msg = (_LE("Error contacting xcat3 server: %(error)s. "
                           "Attempt %(attempt)d of %(total)d") %
                       {'attempt': attempt,
                        'total': num_attempts,
                        'error': error})
                if attempt == num_attempts:
                    LOG.error(msg)
                    raise
                else:
                    LOG.debug(msg)
                    time.sleep(self.conflict_retry_interval)

    return wrapper


class HttpClient(object):
    def __init__(self, endpoint, http_log_debug=False, timings=False,
                 max_retries=DEFAULT_MAX_RETRIES,
                 retry_interval=DEFAULT_RETRY_INTERVAL,
                 timeout=600,
                 ca_file=None,
                 cert_file=None,
                 key_file=None,
                 insecure=None, **kwargs):
        self.endpoint_trimmed = _trim_endpoint_api_version(endpoint)
        self.session = requests.Session()
        self.http_log_debug = http_log_debug
        self.conflict_max_retries = kwargs.pop('max_retries',
                                               DEFAULT_MAX_RETRIES)
        self.conflict_retry_interval = kwargs.pop('retry_interval',
                                                  DEFAULT_RETRY_INTERVAL)
        if insecure:
            self.verify_cert = False
        else:
            if ca_file:
                self.verify_cert = ca_file
            else:
                self.verify_cert = True
            self.cert_file = cert_file
            self.key_file = key_file
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.timeout = timeout
        self.times = []  # [("item", starttime, endtime), ...]
        self.timings = timings

    def http_log_req(self, method, url, kwargs):
        string_parts = ['curl -g -i']

        if not kwargs.get('verify', True):
            string_parts.append(' --insecure')
        string_parts.append(' -X %s' % method)

        headers = copy.deepcopy(kwargs['headers'])
        string_parts.append(' -H %s' % headers)

        if 'data' in kwargs:
            data = json.loads(kwargs['data'])
            string_parts.append(" -d '%s'" % json.dumps(data))

        LOG.debug("REQ: %s" % "".join(string_parts))

    def http_log_resp(self, resp):
        if not self.http_log_debug:
            return

        if resp.text and resp.status_code != 400:
            try:
                body = json.loads(resp.text)
            except ValueError:
                body = None
        else:
            body = None

        self._logger.debug("RESP: [%(status)s] %(headers)s\nRESP BODY: "
                           "%(text)s\n", {'status': resp.status_code,
                                          'headers': resp.headers,
                                          'text': json.dumps(body)})

    @with_retries
    def request(self, url, method, **kwargs):
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        kwargs['headers']['Accept'] = 'application/json'
        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            body = kwargs.pop('body')
            if body:
                kwargs['data'] = json.dumps(body)

        kwargs['verify'] = self.verify_cert
        url = urlparse.urljoin(self.endpoint_trimmed, url)
        self.http_log_req(method, url, kwargs)

        request_func = self.session.request
        resp = request_func(method, url, timeout=3600.0, **kwargs)

        self.http_log_resp(resp)

        if resp.text:
            if resp.status_code == 400:
                if ('Connection refused' in resp.text or
                            'actively refused' in resp.text):
                    raise exception.ConnectionRefused(resp.text)
            try:
                body = json.loads(resp.text)
            except ValueError:
                body = None
        else:
            body = None

        if resp.status_code >= 400:
            raise exception.from_response(resp, body, url, method)

        return resp, body

    def _time_request(self, url, method, **kwargs):
        with utils.record_time(self.times, self.timings, method, url):
            resp, body = self.request(url, method, **kwargs)
        return resp, body

    def get(self, url, **kwargs):
        return self._time_request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        return self._time_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._time_request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._time_request(url, 'DELETE', **kwargs)

    def patch(self, url, **kwargs):
        return self._time_request(url, 'PATCH', **kwargs)


def _construct_http_client(endpoint=None,
                           max_retries=DEFAULT_MAX_RETRIES,
                           retry_interval=DEFAULT_RETRY_INTERVAL,
                           timeout=600,
                           ca_file=None,
                           cert_file=None,
                           key_file=None,
                           insecure=None):
    return HttpClient(endpoint=endpoint,
                      max_retries=max_retries,
                      retry_interval=retry_interval,
                      timeout=timeout,
                      ca_file=ca_file,
                      cert_file=cert_file,
                      key_file=key_file,
                      insecure=insecure)
