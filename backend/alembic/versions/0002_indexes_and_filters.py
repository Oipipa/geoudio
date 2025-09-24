from alembic import op

revision = "0002_indexes_and_filters"
down_revision = "0001_init"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE INDEX IF NOT EXISTS ix_events_ts_start ON events USING btree (ts_start)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_events_geom ON events USING gist (geom)")

def downgrade():
    pass
