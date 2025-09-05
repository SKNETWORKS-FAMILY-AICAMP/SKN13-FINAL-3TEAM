from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="update_car_data",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["db", "import", "crawling"],
) as dag:
    crawl_reviews_task = BashOperator(
        task_id="crawl_car_reviews",
        bash_command="python /app/airflow/scripts/crawling_customer_with_stars.py",
    )

    import_data_task = BashOperator(
        task_id="import_car_data",
        bash_command="docker-compose exec django_gunicorn python manage.py import_data",
    )

    crawl_reviews_task >> import_data_task
