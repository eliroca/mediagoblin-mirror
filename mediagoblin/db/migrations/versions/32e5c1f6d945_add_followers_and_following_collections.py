"""Add followers and following collections

Revision ID: 32e5c1f6d945
Revises: 7adda7ac1de
Create Date: 2016-03-07 12:36:14.446563

"""

# revision identifiers, used by Alembic.
revision = '32e5c1f6d945'
down_revision = '7adda7ac1de'

import datetime

from alembic import op
from sqlalchemy import MetaData, Column, Integer, ForeignKey, and_, or_
from mediagoblin.db.migration_tools import inspect_table

# constants which shouldn't change, these are the values of the collection type
# at the time of writing this migration. (i.e. don't change these - ever).
FOLLOWER_TYPE = "core-followers"
FOLLOWING_TYPE = "core-following"

def upgrade():
    """ Adds the following and followers collections for all LocalUsers """
    # Add the followers and following foreign keys on LocalUser
    followers_column = Column(
        "followers",
        Integer,
        ForeignKey("core__collections.id"),
        nullable=True
    )
    op.add_column("core__local_users", followers_column)

    following_column = Column(
        "following",
        Integer,
        ForeignKey("core__collections.id"),
        nullable=True
    )
    op.add_column("core__local_users", following_column)


    db = op.get_bind()
    metadata = MetaData(bind=db)
    localuser_table = inspect_table(metadata, "core__local_users")
    collection_table = inspect_table(metadata, "core__collections")
    users = list(db.execute(localuser_table.select()))
    for user in users:
        now = datetime.datetime.utcnow()
        followers = db.execute(collection_table.insert().values(
            title="Followers of {username}".format(username=user.username),
            created=now,
            updated=now,
            actor=user.id,
            num_items=0,
            type=FOLLOWER_TYPE
        )).inserted_primary_key[0]

        # Make the following collection.
        following = db.execute(collection_table.insert().values(
            title="Following of {username}".format(username=user.username),
            created=now,
            updated=now,
            actor=user.id,
            num_items=0,
            type=FOLLOWING_TYPE
        )).inserted_primary_key[0]

        # Add the followers and following onto the user.
        db.execute(localuser_table.update().where(
            localuser_table.c.id == user.id
        ).values(
            followers=followers,
            following=following
        ))

    # Modify following and followers to make them not-null
    op.alter_column("core__local_users", "followers", nullable=False)
    op.alter_column("core__local_users","following", nullable=False)

def downgrade():
    """ Removes the followers and following collection """
    db = op.get_bind()
    metadata = MetaData(bind=db)
    localuser_table = inspect_table(metadata, "core__local_users")
    collection_table = inspect_table(metadata, "core__collections")
    collectionitem_table = inspect_table(metadata, "core__collection_items")

    users = list(db.execute(localuser_table.select()))
    for user in users:
        # Delete all the CollectionItems for this users' follower and follwoing
        db.execute(collectionitem_table.delete().where(or_(
            collectionitem_table.c.collection == user.following,
            collectionitem_table.c.collection == user.followers
        )))

        # Remove the collection itself.
        db.execute(collection_table.delete().where(or_(
            collection_table.c.id == user.followers,
            collection_table.c.id == user.followers
        )))

    # Now remove the fields on LocalUser
    op.remove_column("core__local_users", "following")
    op.remove_column("core__local_users", "followers")
