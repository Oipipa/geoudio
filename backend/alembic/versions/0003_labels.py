from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_labels"
down_revision = "0002_indexes_and_filters"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_labels_event_id", "labels", ["event_id"])
    op.create_index("ix_labels_created_at", "labels", ["created_at"])
    op.create_check_constraint("ck_labels_source", "labels", "source IN ('user','system')")

def downgrade():
    op.drop_constraint("ck_labels_source", "labels", type_="check")
    op.drop_index("ix_labels_created_at", table_name="labels")
    op.drop_index("ix_labels_event_id", table_name="labels")
    op.drop_table("labels")
