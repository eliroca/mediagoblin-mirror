"""add inbox and outbox to user

Revision ID: 302927e40930
Revises: cdfbf2e227
Create Date: 2016-03-02 11:12:49.778668

"""

# revision identifiers, used by Alembic.
revision = '302927e40930'
down_revision = 'cdfbf2e227'

import datetime

from alembic import op
from sqlalchemy import MetaData, Column, Integer, ForeignKey, and_, or_
from mediagoblin.db.migration_tools import inspect_table

def upgrade():
    """ Adds the LocalUser.inbox and LocalUser.outbox"""
    inbox_column = Column(
        "inbox",
        Integer,
        ForeignKey("core__collections.id"),
        nullable=True # remove after we've populated.
    )
    op.add_column("core__local_users", inbox_column)

    outbox_column = Column(
        "outbox",
        Integer,
        ForeignKey("core__collections.id"),
        nullable=True # remove after we've populated.
    )
    op.add_column("core__local_users", outbox_column)

    # Now iterate through all the users and create a column for them.
    db = op.get_bind()
    metadata = MetaData(bind=db)
    localuser_table = inspect_table(metadata, "core__local_users")
    collection_table = inspect_table(metadata, "core__collections")
    collectionitem_table = inspect_table(metadata, "core__collection_items")
    activity_table = inspect_table(metadata, "core__activities")
    gmr_table = inspect_table(metadata, "core__generic_model_reference")

    # Get all the users
    users = list(db.execute(localuser_table.select()))
    for user in users:
        now = datetime.datetime.utcnow()
        # Add an inbox collection for the user.
        inbox = db.execute(collection_table.insert().values(
            title="Inbox for {username}".format(username=user.username),
            created=now,
            updated=now,
            actor=user.id,
            num_items=0,
            type="core-inbox"
        )).inserted_primary_key[0]

        # Add an outbox for the user
        outbox = db.execute(collection_table.insert().values(
            title="Outbox for {username}".format(username=user.username),
            created=now,
            updated=now,
            actor=user.id,
            num_items=0,
            type="core-outbox"
        )).inserted_primary_key[0]

        # Save this on the local user
        db.execute(localuser_table.update().where(
            localuser_table.c.id == user.id
        ).values(
            inbox=inbox,
            outbox=outbox
        ))

        # Now find all the activities the user has uploaded and add those to
        # the collection, all their activities should also appear in their
        # inbox.
        activities = list(db.execute(activity_table.select()))
        for activity in activities:
            # Find the GMR for the activity (or create it)
            gmr = db.execute(gmr_table.select().where(and_(
                gmr_table.c.obj_pk == activity.id,
                gmr_table.c.model_type == "core__activities"
            ))).first()

            if gmr is None:
                gmr = db.execute(gmr_table.insert().values(
                    obj_pk=activity.id,
                    model_type="core__activities"
                )).inserted_primary_key[0]
            else:
                gmr = gmr.id

            # Add the activity to the inbox
            db.execute(collectionitem_table.insert().values(
                collection=inbox,
                object_id=gmr,
                added=now
            ))

        # Okay now we need to set the number of items
        db.execute(collection_table.update().where(
            collection_table.c.id == inbox
        ).values(
            num_items=len(activities)
        ))

    # Okay now make inbox and outbox NOT NULL as all users should have them.
    op.alter_column("core__local_users", "inbox", nullable=False)
    op.alter_column("core__local_users", "outbox", nullable=False)

def downgrade():
    """ Remove LocalUser.inbox and LocalUser.outbox and collections """
    db = op.get_bind()
    metadata = MetaData(bind=db)
    collection_table = inspect_table(metadata, "core__collections")
    collectionitem_table = inspect_table(metadata, "core__collection_items")
    localuser_table = inspect_table(metadata, "core__local_users")

    users = db.execute(localuser.select())
    for user in users:
        # Delete the collection items.
        db.execute(collectionitem_table.delete().where(or_(
            collectionitem_table.c.collection == user.inbox,
            collectionitem_table.c.collection == user.outbox
        )))

    # Delete the collection themselves.
    db.execute(collection_table.delete().where(or_(
        collection_table.c.type == "core-inbox",
        collection_table.c.type == "core-outbox"
    )))

    op.drop_column("core__local_users", "inbox")
    op.drop_column("core__local_users", "outbox")
