# Google News Data Pipeline
A simple coded data pipeline to transfer data from Google News to Amazon S3 while creating a data lake for refining information between layers. All project is built using Apache Airflow and Amazon EC2.
The project is divided into three steps which involve mounting and configuring EC2 to initialize Airflow, and running the Python script in cloud to store the results in a bucket

## Table of Contents

- [Requirements](#requirements)
- [Installing Airflow on EC2](#Configuration)
- [Writing the Python DAG](#dag)
- [Opening in S3](#s3)

# Requirements

AWS Account with Access Key and Secret Acces Key configured.
S3 Bucket for project's landing data already created.

# Installing Airflow on EC2 (#Configuration)

First step is create our EC2 instance with Amazon Linux in AWS (I recommend choosing a t2.large or higher for best Docker usage).

Then, connect to your VM through 'Connect' in EC2 options and run these commands:


### Update Linux<br>
sudo yum update

### Install Python and Pip<br>
sudo yum install pip<br>
sudo yum install python3<br>

### Install Docker<br>
sudo yum install docker -y<br>

### Install Docker-Compose latest version<br>
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)"  -o /usr/local/bin/docker-compose<br>
sudo mv /usr/local/bin/docker-compose /usr/bin/docker-compose<br>
sudo chmod +x /usr/bin/docker-compose<br>

### Once you have started the Docker service, you can verify that it is running by running the following command in your terminal:<br>
sudo systemctl start docker<br>
sudo docker run hello-world<br>

### To start the Docker service automatically when the instance starts, you can use the following command:<br>
sudo systemctl enable docker<br>

## Airflow Steps:<br>

### Download docker-compose.yaml from the airflow documentation<br>
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.8.1/docker-compose.yaml'<br>

### Edit docker-compose to allow building requirements.txt<br>
vim docker-compose.yaml<br>
  #comment these row (add # at the beginning)<br>
  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.8.1}<br>
  #uncomment that (remove # from the beginning)<br>
  #build: .<br>

  It should be like this<br>
 ```
...
x-airflow-common:
  &airflow-common
  # In order to add custom dependencies or upgrade provider packages you can use your extended image.
  # Comment the image line, place your Dockerfile in the directory where you placed the docker-compose.yaml
  # and uncomment the "build" line below, Then run `docker-compose build` to build the images.
  #image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.8.1}
  build: .
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
...
```
  #save with !w and exit with !qa:

### Create airflow folders and env<br>
mkdir -p ./dags ./logs ./plugins ./config<br>
echo -e "AIRFLOW_UID=$(id -u)" > .env<br>

### Set Python libraries to install<br>
touch requirements.txt<br>
vim requirements.txt<br>
```
  pandas
  GoogleNews
  boto3
```
!w<br>
!qa:<br>

### Set Dockerfile<br>
touch Dockerfile<br>
vim Dockerfile<br>
  ```
  FROM apache/airflow:2.8.1
  COPY requirements.txt  .
  RUN pip install -r "requirements.txt"
  ```
!w<br>
!qa:<br>

### Install Airflow<br>
docker compose up airflow-init<br>

### Run Airflow<br>
docker compose up<br>

### Allowing access to Airflow UI<br>
Go to 'Security' menu in the EC2 console and alter 'Inbound Rules'. Choose 'Custom TCP rule' in the dropdown then you will be able to change the port to 8080.<br>
Get VM's public url and then put ':8080' at the end of it. You should be able to access Airflow interface.

# Setting environment variables in Airflow

We will then get our AWS keys, the s3 bucket destination path and the terms we want GoogleNews to search and create them

# Creating the DAG

```
# Importing required libraries
import datetime as dt
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
#import boto3
#import awswrangler
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

            for j in list(range(1,2)):
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
        database=landing, #this will be our raw/landing zone
        mode = "append", #incremental adding
        table=google_news,
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

  ```

### Creating dag file in EC2

Then we have to connect again to our EC2 throught 'Connect' and run these commands:
 ```
  cd dags
  touch gnews.py
  copy the script inside the file
  !w
  !qa
```
