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
    
    # 1. 증분 크롤링 (매일 첫 페이지만)
    crawl_reviews_task = BashOperator(
        task_id="crawl_car_reviews_incremental",
        bash_command="""
        echo "📅 매일 첫 페이지만 크롤링합니다"
        python /app/airflow/scripts/incremental_crawling.py 1 1
        """,
    )

    # 2. DB 데이터 임포트 (리뷰 + 집계)
    import_data_task = BashOperator(
        task_id="import_car_data",
        bash_command="docker exec babsim_django_gunicorn_1 python manage.py import_data",
    )

    crawl_reviews_task >> import_data_task
