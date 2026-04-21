from __future__ import annotations

import argparse
import logging
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from paragon_agent.config import settings
from paragon_agent.db import get_conn, init_db
from paragon_agent.pipeline import run_pipeline


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("paragon-agent")


def execute_run() -> None:
    conn = get_conn(settings.db_path)
    init_db(conn)
    result = run_pipeline(conn)
    logger.info("Run complete: %s", result)


def run_scheduler() -> None:
    scheduler = BlockingScheduler(timezone=settings.timezone)
    trigger = CronTrigger(hour=10, minute=0)
    scheduler.add_job(execute_run, trigger=trigger, id="daily_paragon_run", replace_existing=True)
    logger.info("Scheduler running: daily at 10:00 AM in timezone %s", settings.timezone)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown(wait=False)


def init_database() -> None:
    conn = get_conn(settings.db_path)
    init_db(conn)
    logger.info("Database initialized at %s", settings.db_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Paragon Estimating lead agent")
    parser.add_argument("command", choices=["run-once", "run-scheduler", "init-db"])
    args = parser.parse_args()

    if args.command == "run-once":
        execute_run()
    elif args.command == "run-scheduler":
        run_scheduler()
    elif args.command == "init-db":
        init_database()
    else:
        time.sleep(0.1)


if __name__ == "__main__":
    main()

