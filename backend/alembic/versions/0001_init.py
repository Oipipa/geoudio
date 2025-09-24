from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2.types import Geography

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("node_id", sa.String(), nullable=False),
        sa.Column("ts_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ts_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("cls", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("feat_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("geom", Geography(geometry_type="POINT", srid=4326), nullable=False),
    )
    op.create_index("ix_events_node_id", "events", ["node_id"])
    op.create_index("ix_events_ts_start", "events", ["ts_start"])
    op.create_index("ix_events_ts_end", "events", ["ts_end"])
    op.create_index("ix_events_cls", "events", ["cls"])
    op.create_index("ix_events_geom", "events", ["geom"], postgresql_using="gist")

def downgrade():
    op.drop_index("ix_events_geom", table_name="events")
    op.drop_index("ix_events_cls", table_name="events")
    op.drop_index("ix_events_ts_end", table_name="events")
    op.drop_index("ix_events_ts_start", table_name="events")
    op.drop_index("ix_events_node_id", table_name="events")
    op.drop_table("events")
    op.execute("DROP EXTENSION IF EXISTS postgis")
