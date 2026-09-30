"""Versioned installation and guarded adoption of the original schema."""
import argparse
import importlib.util
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parents[1]


def config(connection):
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["connection"] = connection
    return cfg


def schema_signature(connection):
    inspector = inspect(connection)
    result = {}
    for table in sorted(set(inspector.get_table_names()) - {"alembic_version"}):
        columns = {
            c["name"]: (c["type"]._type_affinity.__name__, c["nullable"],
                        getattr(c["type"], "length", None))
            for c in inspector.get_columns(table)
        }
        unique = {tuple(c["column_names"]) for c in inspector.get_unique_constraints(table)}
        unique.update(tuple(c["column_names"]) for c in inspector.get_indexes(table) if c["unique"])
        foreign = sorted((tuple(c["constrained_columns"]), c["referred_table"],
                          tuple(c["referred_columns"])) for c in inspector.get_foreign_keys(table))
        result[table] = (columns, sorted(unique), foreign,
                         inspector.get_pk_constraint(table)["constrained_columns"])
    return result


def install_baseline(connection):
    spec = importlib.util.spec_from_file_location("frozen_baseline", ROOT / "migrations/versions/0001_baseline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with Operations.context(MigrationContext.configure(connection)):
        module.upgrade()


def adopt_legacy(connection):
    if "alembic_version" in inspect(connection).get_table_names():
        raise RuntimeError("BD já versionada; use upgrade.")
    reference = create_engine("sqlite:///:memory:")
    try:
        with reference.begin() as expected:
            install_baseline(expected)
            if schema_signature(connection) != schema_signature(expected):
                raise RuntimeError("Esquema diferente da base inicial; adopção recusada. Rever uma cópia da BD.")
    finally:
        reference.dispose()
    command.stamp(config(connection), "0001")


def assert_current(connection):
    from alembic.script import ScriptDirectory
    if MigrationContext.configure(connection).get_current_heads() != tuple(ScriptDirectory.from_config(config(connection)).get_heads()):
        raise RuntimeError("BD desactualizada. Execute python -m app.migrate upgrade antes de arrancar.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["upgrade", "adopt", "check"])
    args = parser.parse_args()
    from app.core.database import engine
    with engine.begin() as connection:
        if args.action == "adopt":
            adopt_legacy(connection)
        elif args.action == "upgrade":
            command.upgrade(config(connection), "head")
        else:
            assert_current(connection)


if __name__ == "__main__":
    main()
