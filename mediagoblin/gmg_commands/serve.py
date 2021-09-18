# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

from paste.script.command import get_commands, invoke


def parser_setup(subparser):
    # Duplicating these arguments so that `gmg serve` will accept them and
    # provide command-line help. We don't actually used the parsed arguments.
    subparser.add_argument('config', metavar='CONFIG_FILE')
    subparser.add_argument('command',
                           choices=['start', 'stop', 'restart', 'status'],
                           nargs='?', default='start')
    subparser.add_argument('-n', '--app-name',
                           dest='app_name',
                           metavar='NAME',
                           help="Load the named application (default main)")
    subparser.add_argument('-s', '--server',
                           dest='server',
                           metavar='SERVER_TYPE',
                           help="Use the named server.")
    subparser.add_argument('--reload',
                           dest='reload',
                           action='store_true',
                           help="Use auto-restart file monitor")


def serve(args):
    # Option 1: Run Paste Script's ServeCommand from Python.
    #
    # Taking the lead from paste.script.command.run and re-using their "serve"
    # command. We don't have an easy way to feed the already parsed arguments
    # through though, so we're pulling these directly from argv.
    args = sys.argv
    args_after_subcommand = args[args.index('serve') + 1:]
    command = get_commands()['serve'].load()
    invoke(command, 'serve', {}, args_after_subcommand)

    # Option 2: Serve with Waitress.
    #
    # Works but has no reloading capabilities but unlike Paste Script doesn't know where to
    # find the static files.
    #
    # Hupper has an example of waitress + reloading:
    # https://docs.pylonsproject.org/projects/hupper/en/master/#api-usage
    # from mediagoblin.app import MediaGoblinApp
    # from waitress import serve
    # app = MediaGoblinApp('mediagoblin.ini')
    # serve(app, listen='*:6543')
