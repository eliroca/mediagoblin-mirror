"""add user column to client

Revision ID: cdfbf2e227
Revises: bc5a5d4f421
Create Date: 2016-03-01 15:00:34.511009

"""

# revision identifiers, used by Alembic.
revision = 'cdfbf2e227'
down_revision = 'bc5a5d4f421'

from alembic import op
from sqlalchemy import MetaData, Unicode, Column, Integer, ForeignKey
from mediagoblin.db.migration_tools import inspect_table

def upgrade():
    """ Add the Client.user field """
    user_column = Column(
        "user",
        Integer,
        ForeignKey("core__users.id"),
        nullable=True
    )
    op.add_column("core__clients", user_column)
    host_column = Column(
        "host",
        Unicode,
        nullable=True
    )
    op.add_column("core__clients", host_column)

def downgrade():
    """ Removes the Client.user field """
    op.drop_column("core__clients", "user")
    op.drop_column("core__clients", "host")
