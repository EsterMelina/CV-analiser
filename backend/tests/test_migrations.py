import sqlite3

import pytest
from alembic import command
from sqlalchemy import create_engine, text

from app.migrate import adopt_legacy, config, install_baseline, schema_signature, assert_current


def test_empty_and_existing_database_converge_and_backup_restores():
    empty = create_engine("sqlite:///:memory:")
    legacy = create_engine("sqlite:///:memory:")
    backup = sqlite3.connect(":memory:")
    try:
        with empty.begin() as connection:
            command.upgrade(config(connection), "head")
            target = schema_signature(connection)
            assert_current(connection)
        with legacy.begin() as connection:
            install_baseline(connection)
            connection.execute(text("INSERT INTO companies (id, name, is_active) VALUES (1, 'Ficticia', 1)"))
        with legacy.connect() as connection:
            connection.connection.driver_connection.backup(backup)
        with legacy.begin() as connection:
            adopt_legacy(connection)
            command.upgrade(config(connection), "head")
            assert schema_signature(connection) == target
            assert connection.execute(text("SELECT name FROM companies WHERE id=1")).scalar() == "Ficticia"
        # Recovery rehearsal: restore the pre-migration backup into a fresh DB.
        restored = sqlite3.connect(":memory:")
        backup.backup(restored)
        assert restored.execute("SELECT name FROM companies").fetchone() == ("Ficticia",)
        assert not restored.execute("SELECT name FROM sqlite_master WHERE name='alembic_version'").fetchone()
        restored.close()
    finally:
        backup.close()
        empty.dispose()
        legacy.dispose()


def test_adoption_refuses_unknown_schema():
    engine = create_engine("sqlite:///:memory:")
    try:
        with engine.begin() as connection:
            install_baseline(connection)
            connection.execute(text("ALTER TABLE companies ADD COLUMN unknown VARCHAR"))
            with pytest.raises(RuntimeError, match="adopção recusada"):
                adopt_legacy(connection)
    finally:
        engine.dispose()


def test_shared_legacy_identity_splits_without_losing_documents_or_profile():
    engine = create_engine("sqlite:///:memory:")
    try:
        with engine.begin() as c:
            command.upgrade(config(c), "0001")
            c.execute(text("INSERT INTO companies (id,name,is_active) VALUES (1,'A',1),(2,'B',1)"))
            c.execute(text("INSERT INTO jobs (id,company_id,title,code,description,job_type,modality,min_experience_years,status) VALUES (1,1,'A','A','A','FULL_TIME','ON_SITE',0,'DRAFT'),(2,2,'B','B','B','FULL_TIME','ON_SITE',0,'DRAFT')"))
            c.execute(text("INSERT INTO candidates (id,name,email) VALUES (1,'Pessoa','person@example.com')"))
            c.execute(text("INSERT INTO applications (id,candidate_id,job_id,source,status) VALUES (1,1,1,'UPLOAD','RECEIVED'),(2,1,2,'UPLOAD','RECEIVED')"))
            c.execute(text("INSERT INTO resumes (id,application_id,original_filename,stored_path) VALUES (1,1,'a.pdf','a.pdf'),(2,2,'b.pdf','b.pdf')"))
            c.execute(text("INSERT INTO candidate_skills (id,candidate_id,name,confidence) VALUES (1,1,'legacy',1)"))
            command.upgrade(config(c), "head")
            assert c.execute(text("SELECT count(*) FROM candidates")).scalar() == 3
            assert c.execute(text("SELECT count(distinct candidate_id) FROM applications")).scalar() == 2
            assert c.execute(text("SELECT count(*) FROM resumes")).scalar() == 2
            assert c.execute(text("SELECT candidate_id FROM candidate_skills")).scalar() == 1
            assert c.execute(text("SELECT company_id FROM candidates WHERE id=1")).scalar() is None
    finally:
        engine.dispose()
