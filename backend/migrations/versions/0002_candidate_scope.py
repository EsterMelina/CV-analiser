"""Separate candidate identity by company, retaining ambiguous legacy profiles."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("candidates") as batch:
        batch.drop_index("ix_candidates_email")
        batch.add_column(sa.Column("company_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("legacy_candidate_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_candidates_company", "companies", ["company_id"], ["id"])
        batch.create_index("ix_candidates_company_id", ["company_id"])
        batch.create_index("ix_candidates_email", ["email"], unique=False)
        batch.create_unique_constraint("uq_candidate_company_email", ["company_id", "email"])
    connection = op.get_bind()
    metadata = sa.MetaData()
    candidates = sa.Table("candidates", metadata, autoload_with=connection)
    applications = sa.Table("applications", metadata, autoload_with=connection)
    jobs = sa.Table("jobs", metadata, autoload_with=connection)
    for candidate in connection.execute(sa.select(candidates)).mappings().all():
        companies = connection.execute(sa.select(jobs.c.company_id).join(
            applications, applications.c.job_id == jobs.c.id
        ).where(applications.c.candidate_id == candidate["id"]).distinct()).scalars().all()
        if len(companies) == 1:
            connection.execute(candidates.update().where(candidates.c.id == candidate["id"]).values(company_id=companies[0]))
        elif len(companies) > 1:
            # Retain original and its mixed profile in admin-only quarantine.
            # Do not distribute a potentially overwritten profile to tenants.
            for company_id in companies:
                new_id = connection.execute(candidates.insert().values(
                    company_id=company_id, legacy_candidate_id=candidate["id"],
                    name=candidate["name"], email=candidate["email"],
                    created_at=candidate["created_at"], updated_at=candidate["updated_at"],
                )).inserted_primary_key[0]
                company_jobs = sa.select(jobs.c.id).where(jobs.c.company_id == company_id)
                connection.execute(applications.update().where(
                    applications.c.candidate_id == candidate["id"], applications.c.job_id.in_(company_jobs)
                ).values(candidate_id=new_id))


def downgrade():
    raise RuntimeError("Restaurar backup anterior; reunir identidades perderia isolamento.")
