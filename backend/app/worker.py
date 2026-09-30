"""Durable worker. Supervisor deadline accommodates the configured local model."""
import argparse
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.once:
        from app.core.database import SessionLocal, engine
        from app.migrate import assert_current
        from app.services.executions import process_one
        with engine.connect() as connection:
            assert_current(connection)
        with SessionLocal() as db:
            process_one(db)
        return
    while True:
        try:
            from app.services.executions import execution_timeout
            subprocess.run([sys.executable, "-m", "app.worker", "--once"], timeout=execution_timeout(), check=False)
        except subprocess.TimeoutExpired:
            print("Worker excedeu prazo; a execução será recuperada após expirar a reserva.", flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
