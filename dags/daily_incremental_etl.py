from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pendulum
from airflow.sdk import dag, task
from airflow.providers.standard.operators.bash import BashOperator
from airflow.exceptions import AirflowSkipException

from extract.extract_incremental import (
    read_watermark,
    write_watermark,
    list_pending_dates,
    extract,
    validate,
    load,
)


@dag(
    dag_id="daily_incremental_etl",
    schedule="@daily",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    default_args={"retries": 3, "retry_delay": pendulum.duration(minutes=5)},
    tags=["etl", "incremental"],
)
def daily_incremental_etl():

    @task
    def extract_task() -> dict:
        watermark = read_watermark()
        pending_dates = list_pending_dates(watermark)
        if not pending_dates:
            raise AirflowSkipException("No data updated, skip extraction")

        df = extract(pending_dates)
        Path("landing").mkdir(exist_ok=True)
        staging_path = "landing/_staging.csv"
        df.to_csv(staging_path, index=False)

        return {
            "staging_path": staging_path,
            "dates": [d.isoformat() for d in pending_dates],
        }

    @task
    def validate_task(batch: dict | None) -> dict | None:
        df = pd.read_csv(batch["staging_path"])
        validate(df)
        return batch

    @task
    def load_task(batch: dict | None) -> None:
        df = pd.read_csv(batch["staging_path"])
        pending_dates = [date.fromisoformat(s) for s in batch["dates"]]
        load(df, pending_dates)
        write_watermark(pending_dates[-1])

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="echo 'dbt run 占位符，等 dbt 项目接进来之后换成真的 dbt run'",
    )

    batch = extract_task()
    validated = validate_task(batch)
    load_task(validated) >> dbt_run


daily_incremental_etl()
