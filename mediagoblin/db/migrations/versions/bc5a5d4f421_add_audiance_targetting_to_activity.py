"""Add audiance targetting to Activity


Revision ID: bc5a5d4f421
Revises: 228916769bd2
Create Date: 2016-01-21 10:56:20.493545

"""

# revision identifiers, used by Alembic.
revision = 'bc5a5d4f421'
down_revision = '228916769bd2'

from alembic import op
from sqlalchemy import MetaData, Column, Integer, ForeignKey
from mediagoblin.db.migration_tools import inspect_table

def upgrade():
    # Add Activity.to
    to_column = Column(
        "to",
        Integer,
        ForeignKey("core__collections.id")
    )
    op.add_column("core__activities", to_column)

    # Add cc column
    cc_column = Column(
        "cc",
        Integer,
        ForeignKey("core__collections.id")
    )
    op.add_column("core__activities", cc_column)

    # Add bto column
    bto_column = Column(
        "bto",
        Integer,
        ForeignKey("core__collections.id")
    )
    op.add_column("core__activities", bto_column)

    # Add bcc column
    bcc_column = Column(
        "bcc",
        Integer,
        ForeignKey("core__collections.id")
    )
    op.add_column("core__activities", bcc_column)

    # Now remove the nullable constraint on Collection.actor
    op.alter_column("core__collections", "actor", nullable=True)

    # Now add activities to a collection containing just "Public" as that's
    # what they are before we got the access controls
    db = op.get_bind()
    metadata = MetaData(bind=db)
    activity_table = inspect_table(metadata, "core__activities")
    collection_table = inspect_table(metadata, "core__collections")
    for activity in db.execute(activity_table.select()):
        now = datetime.datetime.utcnow()

        # Add a collection for the activity
        to_collection = db.execute(collection_table.insert().values(
            title="Activity 'to' audiance",
            created=now,
            updated=now,
            type="core-audience-targetting"
        )).inserted_primary_key[0]

        db.execute(activity_table.update().where(
            activity_table.c.id == activity.id
        ).values(
            to=to_collection
        ))

        # Add the public collection to the "to" collection
        public_collection = db.execute(collection_table.select().where(and_(
            collection_table.c.public_id == "http://activityschema.org/collection/public",
            collection_table.c.type == "core-public"
        ))).first()

        # check if there is a GMR
        public_gmr = db.execute(gmr_table.select().where(_and(
            gmr_table.c.obj_pk == public_collection.id,
            gmr_table.c.model_type == "core__collections"
        ))).first()

        # In the unlikely event this doesn't exist we should create it
        if public_gmr == None:
            public_gmr = db.execute(gmr_table.insert().values(
                obj_pk=public_collection.id,
                model_type="core__collections"
            )).inserted_primary_key[0]
        else:
            public_gmr = public_gmr.id

        public_ci = db.execute(collection_item_table.insert().values(
            object_id=public_gmr,
            collection=public_collection.id,
            added=now,
            position=0
        ))


def downgrade():
    op.drop_column("core__activities", "to")
    op.drop_column("core__activities", "cc")
    op.drop_column("core__activities", "bto")
    op.drop_column("core__activities", "bcc")

    # Remove all collections without actors so we can change it to be nullable
    db = op.get_bind()
    metadata = MetaData(bind=db)
    collection_table = inspect_table(metadata, "core__collections")

    db.execute(collection_table.delete().where(
        collection_table.c.actor == None
    ))

    # Remove the nullable constraint
    op.alter_column("core__collections", "actor", nullable=False)
