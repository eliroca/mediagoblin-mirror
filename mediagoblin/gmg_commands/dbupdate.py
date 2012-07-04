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

from sqlalchemy.orm import sessionmaker

from mediagoblin.db.sql.open import setup_connection_and_db_from_config
from mediagoblin.db.sql.util import MigrationManager
from mediagoblin.init import setup_global_and_app_config
from mediagoblin.tools.common import import_component


def dbupdate_parse_setup(subparser):
    pass


class DatabaseData(object):
    def __init__(self, name, models, migrations):
        self.name = name
        self.models = models
        self.migrations = migrations

    def make_migration_manager(self, session):
        return MigrationManager(
            self.name, self.models, self.migrations, session)


def gather_database_data(media_types):
    """
    Gather all database data relevant to the extensions we have
    installed so we can do migrations and table initialization.

    Returns a list of DatabaseData objects.
    """
    managed_dbdata = []

    # Add main first
    from mediagoblin.db.sql.models import MODELS as MAIN_MODELS
    from mediagoblin.db.sql.migrations import MIGRATIONS as MAIN_MIGRATIONS

    managed_dbdata.append(
        DatabaseData(
            u'__main__', MAIN_MODELS, MAIN_MIGRATIONS))

    # Then get all registered media managers (eventually, plugins)
    for media_type in media_types:
        models = import_component('%s.models:MODELS' % media_type)
        migrations = import_component('%s.migrations:MIGRATIONS' % media_type)
        managed_dbdata.append(
            DatabaseData(media_type, models, migrations))

    return managed_dbdata


def run_dbupdate(app_config):
    """
    Initialize or migrate the database as specified by the config file.

    Will also initialize or migrate all extensions (media types, and
    in the future, plugins)
    """

    # Gather information from all media managers / projects
    dbdatas = gather_database_data(app_config['media_types'])

    # Set up the database
    connection, db = setup_connection_and_db_from_config(app_config)

    Session = sessionmaker(bind=db.engine)

    # Setup media managers for all dbdata, run init/migrate and print info
    # For each component, create/migrate tables
    for dbdata in dbdatas:
        migration_manager = dbdata.make_migration_manager(Session())
        migration_manager.init_or_migrate()


def dbupdate(args):
    global_config, app_config = setup_global_and_app_config(args.conf_file)
    run_dbupdate(app_config)
