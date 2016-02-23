"""Add MediaFile.file_url

Revision ID: 7adda7ac1de
Revises: 302927e40930
Create Date: 2016-03-03 22:43:58.280446

"""

# revision identifiers, used by Alembic.
revision = '7adda7ac1de'
down_revision = '302927e40930'

from alembic import op
from sqlalchemy import Column, Unicode

def upgrade():
    """ Adds the MediaFile.file_url field """
    file_url = Column(
        "file_url",
        Unicode,
        nullable=True
    )
    op.add_column("core__mediafiles", file_url)


def downgrade():
    """ Removes the MediaFile.file_url field """
    op.remove_column("core__mediafiles", "file_url")
