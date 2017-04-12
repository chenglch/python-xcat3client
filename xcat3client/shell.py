#    Updated 2017 for xcat test purpose
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
Command-line interface to xCAT3 API.
"""

from __future__ import print_function

import argparse
import logging
import sys
from oslo_utils import encodeutils
import six
import traceback

import xcat3client
from xcat3client import client as xcatclient
from xcat3client.common import cliutils
from xcat3client.common import http
from xcat3client.common.i18n import _
from xcat3client.common import utils
from xcat3client import exc

LATEST_API_VERSION = ('1', 'latest')

class XCAT3Shell(object):

    def get_base_parser(self):
        parser = argparse.ArgumentParser(
            prog='xcat3',
            description=__doc__.strip(),
            epilog='See "xcat3 help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=HelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h', '--help',
                            action='store_true',
                            help=argparse.SUPPRESS,
                            )

        parser.add_argument('--version',
                            action='version',
                            version=xcat3client.__version__)

        parser.add_argument('--debug',
                            default=bool(cliutils.env('XCAT3CLIENT_DEBUG')),
                            action='store_true',
                            help='Defaults to env[XCAT3CLIENT_DEBUG]')

        parser.add_argument('--json',
                            default=False,
                            action='store_true',
                            help='Print JSON response without formatting.')

        parser.add_argument('-v', '--verbose',
                            default=False, action="store_true",
                            help="Print more verbose output")

        parser.add_argument('--xcat3-url',
                            default=cliutils.env('XCAT3_URL'),
                            help='Defaults to env[XCAT3_URL]')

        parser.add_argument('--xcat3_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--max-retries', type=int,
                            help='Maximum number of retries in case of '
                            'conflict error (HTTP 409). '
                            'Defaults to env[XCAT3_MAX_RETRIES] or %d. '
                            'Use 0 to disable retrying.'
                            % http.DEFAULT_MAX_RETRIES,
                            default=cliutils.env(
                                'XCAT3_MAX_RETRIES',
                                default=str(http.DEFAULT_MAX_RETRIES)))

        parser.add_argument('--retry-interval', type=int,
                            help='Amount of time (in seconds) between retries '
                            'in case of conflict error (HTTP 409). '
                            'Defaults to env[XCAT3_RETRY_INTERVAL] or %d.'
                            % http.DEFAULT_RETRY_INTERVAL,
                            default=cliutils.env(
                                'XCAT3_RETRY_INTERVAL',
                                default=str(http.DEFAULT_RETRY_INTERVAL)))

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>',
                                           dest='subparser_name')
        submodule = utils.import_versioned_module(version, 'shell')
        submodule.enhance_parser(parser, subparsers, self.subcommands)
        utils.define_commands_from_module(subparsers, self, self.subcommands)
        return parser

    def _setup_debugging(self, debug):
        if debug:
            logging.basicConfig(
                format="%(levelname)s (%(module)s:%(lineno)d) %(message)s",
                level=logging.DEBUG)
        else:
            logging.basicConfig(
                format="%(levelname)s %(message)s",
                level=logging.CRITICAL)


    def do_bash_completion(self):
        commands = set()
        options = set()
        for sc_str, sc in self.subcommands.items():
            commands.add(sc_str)
            for option in sc._optionals._option_string_actions.keys():
                options.add(option)

        commands.remove('bash-completion')
        print(' '.join(commands | options))

    def main(self, argv):
        # Parse args once to find version
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)
        self._setup_debugging(options.debug)

        subcommand_parser = self.get_subcommand_parser('1')
        self.parser = subcommand_parser

        # Handle top-level --help/-h before attempting to parse
        # a command off the command line
        if options.help or not argv:
            self.do_help(options)
            return 0

        # Parse args again and call whatever callback was selected
        args = subcommand_parser.parse_args(argv)

        # Short-circuit and deal with these commands right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion()
            return 0

        if args.max_retries < 0:
            raise exc.CommandError(_("You must provide value >= 0 for "
                                     "--max-retries"))
        if args.retry_interval < 1:
            raise exc.CommandError(_("You must provide value >= 1 for "
                                     "--retry-interval"))
        client_args = ('xcat3_url',)
        kwargs = {}
        for key in client_args:
            kwargs[key] = getattr(args, key)
        if not kwargs.get('xcat3_url'):
            kwargs['xcat3_url'] = 'http://localhost:3010'
        client = xcatclient.get_client(**kwargs)

        try:
            args.func(client, args)
        except exc.CommandError as e:
            subcommand_parser = self.subcommands[args.subparser_name]
            subcommand_parser.error(e)

    @cliutils.arg('command', metavar='<subcommand>', nargs='?',
                  help='Display help for <subcommand>')
    def do_help(self, args):
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError(_("'%s' is not a valid subcommand") %
                                       args.command)
        else:
            self.parser.print_help()


class HelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(HelpFormatter, self).start_section(heading)

def main():
    try:
        XCAT3Shell().main(sys.argv[1:])
    except KeyboardInterrupt:
        print("... terminating xcat3 client", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(encodeutils.safe_encode(six.text_type(e)), file=sys.stderr)
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
