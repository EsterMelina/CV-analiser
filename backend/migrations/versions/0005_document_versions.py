from alembic import op
import sqlalchemy as sa
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("resumes", sa.Column("sha256", sa.String(64), nullable=True))
    op.add_column("resumes", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, application_id FROM resumes ORDER BY application_id, id")).all()
    versions = {}
    for row in rows:
        versions[row.application_id] = versions.get(row.application_id, 0) + 1
        connection.execute(sa.text("UPDATE resumes SET version=:version WHERE id=:id"), {"version": versions[row.application_id], "id": row.id})


def downgrade():
    op.drop_column("resumes", "version")
    op.drop_column("resumes", "sha256")
