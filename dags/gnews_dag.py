# Importing required libraries
import datetime as dt
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
import boto3
import awswrangler as wr
import pandas as pd
from GoogleNews import GoogleNews

# Retrieving variables from Airflow's Variable Store
s3_raw_path = Variable.get("s3_raw_path")
aws_secret_access_key = Variable.get("aws_secret_access_key")
region = Variable.get("aws_region")
terms = Variable.get("terms")
aws_access_key_id = Variable.get("aws_access_key_id")

# Default arguments for the DAG
default_args = {
    'onwer':'viniciusfj',
     #"on_failure_callback": callback.task_fail_slack_alert,
     "retries":3,
     "retry_delay":timedelta(minutes = 5)
}

# Creating a DAG instance using the 'with' context manager
with DAG(
    dag_id = 'gnews_raw',                             # Unique identifier for the DAG
    description = 'DAG to download data from Google News',  # Description of the DAG
    default_args = default_args,                               # Applying the previously defined default arguments
    start_date = dt.datetime.today(),                          # Start date
    schedule_interval = timedelta(days=1),                     # Setting the DAG to run daily
    tags = ['gnews','google','aws']                             # Tags for easy organization and search of the DAG
) as dag:

    # Function to retrieve data from Google News
    def get_data():

        selected_news_all_terms = []

        for i in terms:
            googlenews = GoogleNews(period = 'd', lang = 'en')
            googlenews.clear()
            googlenews.search(i)

            news = []

            for j in list(range(1,15)):
                result = googlenews.page_at(j)
                result = pd.DataFrame(result)
                result['page'] = j
                news.append(result)

            selected_news = pd.concat(news)

        selected_news_all_terms.append(selected_news)
        df = pd.concat(selected_news_all_terms)
        return df
    
    # Function to save retrieved data to AWS S3 in Parquet format
    def save_raw(**kwargs):
        df = kwargs['task_instance'].xcom_pull(task_ids='collect_data')
        # Creating a connection between Python and AWS S3
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )

        s3_client = session.client('s3')
        
        # Writing the DataFrame to Parquet format on S3
        wr.s3.to_parquet(
        df=df,
        path=f"{s3_raw_path}",
        dataset=True,
        database="landing", #this will be our raw/landing zone
        mode = "append", #incremental adding
        table="google_news",
        boto3_session = session #here we use the connection created initially
        )

    # Define the task using the PythonOperator to collect data
    collector = PythonOperator(
        task_id='collect_data',
        python_callable=get_data,
        dag=dag
    )

    # Define the task using the PythonOperator to save data to raw zone
    save_raw = PythonOperator(
        task_id='save_to_raw',
        python_callable=save_raw,
        dag=dag
    )

    # Define the task dependencies
    collector >> save_raw
