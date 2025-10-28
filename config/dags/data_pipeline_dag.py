"""
Apache Airflow DAG for Goodreads Recommendation System Data Pipeline

This DAG orchestrates the complete data processing pipeline for the Goodreads
recommendation system, including data validation, cleaning, feature engineering,
normalization, and data versioning.

Pipeline Flow:
1. Data Reading & Validation - Extract data from BigQuery and validate quality
2. Data Cleaning - Clean and standardize raw data
3. Post-Cleaning Validation - Validate cleaned data quality
4. Feature Engineering - Create ML features from cleaned data
5. Data Normalization - Normalize features for ML algorithms
6. Staging Table Promotion - Move staging tables to production
7. Data Versioning - Track data changes with DVC

Author: Goodreads Recommendation Team
Date: 2025
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from datetime import datetime, timedelta
import os
from airflow.utils.email import send_email
import pytest
import logging

# Import pipeline modules
from datapipeline.scripts.data_cleaning import main as data_cleaning_main
from datapipeline.scripts.feature_engineering import main as feature_engg_main
from datapipeline.scripts.normalization import main as normalization_main
from datapipeline.scripts.anomaly_detection import main_pre_validation, main_post_validation
from datapipeline.scripts.promote_staging_tables import main as promote_staging_main
from datapipeline.scripts.feature_metadata import main as feature_metadata_main
from datapipeline.scripts.train_test_val import main as train_test_split_main

# Default arguments for all DAG tasks
default_args = {
    'owner': 'admin',                    # DAG owner
    'start_date': datetime(2025, 1, 18), # DAG start date
    'retries': 0,                        # Number of retries on failure
    'retry_delay': timedelta(minutes=2), # Delay between retries
    'email_on_failure': False,           # Disable email on failure (handled by callbacks)
    'email_on_retry': False,             # Disable email on retry
}
def send_failure_email(context):
    """
    Send email notification when a DAG task fails.
    
    Args:
        context: Airflow task context containing failure information
    """
    task_instance = context.get('task_instance')
    dag_id = context.get('dag').dag_id
    task_id = task_instance.task_id
    execution_date = context.get('execution_date')
    log_url = task_instance.log_url

    subject = f"[Airflow] DAG {dag_id} Failed: Task {task_id}"
    html_content = f"""
    <p>DAG <b>{dag_id}</b> failed for task <b>{task_id}</b> on {execution_date}.</p>
    <p>Check logs: <a href="{log_url}">Click here</a></p>
    """
    send_email(to=os.environ.get("AIRFLOW__SMTP__SMTP_USER"), subject=subject, html_content=html_content)

def send_success_email(context):
    """
    Send email notification when a DAG completes successfully.
    
    Args:
        context: Airflow task context containing success information
    """
    dag_id = context.get('dag').dag_id
    execution_date = context.get('execution_date')
    subject = f"[Airflow] DAG {dag_id} Succeeded"
    html_content = f"""
    <p>DAG <b>{dag_id}</b> succeeded for execution date {execution_date}.</p>
    """
    send_email(to=os.environ.get("AIRFLOW__SMTP__SMTP_USER"), subject=subject, html_content=html_content)
    
def log_query_results(**kwargs):
    """
    Log the results from the BigQuery data reading task.
    
    This function retrieves the job ID from the previous task and logs
    the query results for monitoring and debugging purposes.
    
    Args:
        **kwargs: Airflow task context
    """
    ti = kwargs['ti']
    job_id = ti.xcom_pull(task_ids='read_data_from_bigquery')

    from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook

    # Get BigQuery client using the configured connection
    hook = BigQueryHook(gcp_conn_id="goodreads_conn")
    client = hook.get_client()

    # Retrieve and log query results
    query_job = client.get_job(job_id)
    rows = list(query_job.result())

    logging.info("Query Results:")
    for row in rows:
        logging.info(dict(row))

def data_cleaning_run():
    data_cleaning_main()

    logging.info("Data cleaning completed")
    logging.info("Running Data Cleaning Tests")

    result = pytest.main(["datapipeline/tests/test_data_cleaning.py", "-q"])
    if result != 0:
        raise Exception("Data Cleaning Tests Failed")
    
    logging.info("Data Cleaning Tests Passed Successfully")

    
def feature_engg_run():
    feature_engg_main()

    logging.info("Feature Engineering completed")
    logging.info("Running Feature Engineering Tests")

    result = pytest.main(["datapipeline/tests/test_feature_engineering.py", "-q"])
    if result != 0:
        raise Exception("Feature Engineering Tests Failed")
    
    logging.info("Feature Engineering Tests Passed Successfully")
    
def normalization_run():
    normalization_main()

    logging.info("Normalization completed")
    logging.info("Running Normalization Tests")

    result = pytest.main(["datapipeline/tests/test_normalization.py", "-q"])
    if result != 0:
        raise Exception("Normalization Tests Failed")

    logging.info("Normalization Tests Passed Successfully")

def data_versioning_run():
    feature_metadata_main()
    
    os.system("dvc add data/metadata/goodreads_features_metadata.json")
    os.system("git add data/metadata/goodreads_features_metadata.json.dvc")
    os.system('git commit -m "Track DVC metadata for features data"')
    # os.system("dvc push")
    # os.system(f"dvc add {data_location}")

    logging.info("Data Versioning completed")

def train_test_split_run():
    train_test_split_main()

    logging.info("Train Test Split completed")

with DAG(
    dag_id='goodreads_recommendation_pipeline',
    default_args=default_args,
    description='Goodreads Recommendation System Data Pipeline',
    catchup=False,
    on_failure_callback=send_failure_email, 
    on_success_callback=send_success_email,  
) as dag:
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ.get("AIRFLOW_HOME")+"/gcp_credentials.json"

    start = EmptyOperator(task_id='start')

    data_reading_task = BigQueryInsertJobOperator(
        task_id='read_data_from_bigquery',
        configuration={
            "query": {
                "query": """
                    SELECT 
                        'books' as table_type,
                        COUNT(*) as record_count
                    FROM `recommendation-system-475301.books.goodreads_books_mystery_thriller_crime`
                    UNION ALL
                    SELECT 
                        'interactions' as table_type,
                        COUNT(*) as record_count
                    FROM `recommendation-system-475301.books.goodreads_interactions_mystery_thriller_crime`
                """,
                "useLegacySql": False,
            }
        },
        gcp_conn_id='goodreads_conn',
    )

    log_results_task = PythonOperator(
        task_id='log_bq_results',
        python_callable=log_query_results,
    )
    
    data_validation_task = PythonOperator(
        task_id='validate_data_quality',
        python_callable=main_pre_validation,
        doc_md="""
        ## Data Validation Task
        Simple data quality checks:
        - Required columns exist
        - Data ranges are valid
        - Missing values within limits
        - Stops pipeline if critical issues found
        """
    )

    data_cleaning_task = PythonOperator(
        task_id='clean_data',
        python_callable=data_cleaning_run,
    )
    
    post_cleaning_validation_task = PythonOperator(
        task_id='validate_cleaned_data',
        python_callable=main_post_validation,
        doc_md="""
        ## Post-Cleaning Validation Task
        Validates data quality after cleaning:
        - Ensures cleaning process worked correctly
        - Checks for any new data quality issues
        - Validates cleaned data meets requirements
        """
    )
     

    feature_engg_task = PythonOperator(
        task_id='feature_engg_data',
        python_callable=feature_engg_run,
    )
    
    normalization_task = PythonOperator(
        task_id='normalize_data',
        python_callable= normalization_run,
    )

    promote_staging_task = PythonOperator(
        task_id='promote_staging_tables',
        python_callable=promote_staging_main,
    )

    data_versioning_task = PythonOperator(
        task_id='data_versioning',
        python_callable=data_versioning_run,
    )

    train_test_split_task = PythonOperator(
        task_id='train_test_split',
        python_callable=train_test_split_run,
    )

    end = EmptyOperator(task_id='end')

    start >> data_reading_task >> log_results_task >> data_validation_task >> data_cleaning_task
    data_cleaning_task >> post_cleaning_validation_task >> feature_engg_task >> normalization_task
    normalization_task >> promote_staging_task >> data_versioning_task >> train_test_split_task >> end
    