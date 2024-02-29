# Google News Data Pipeline
A simple coded data pipeline to transfer data from Google News to Amazon S3 while creating a data lake for refining information between layers. All project is built using Apache Airflow and Amazon EC2.
The project is divided into three steps which involve mounting and configuring EC2 to initialize Airflow, and running the Python script in cloud to store the results in a bucket

![airflow (1)](https://github.com/viniciusfjacinto/google-news-data-pipeline/assets/87664450/45a5c5bb-5bf7-4028-8c74-de958d4fd0dc)

## Table of Contents

- [Requirements](#requirements)
- [EC2-Configuration](#EC2-Configuration)
- [Airflow-Configuration](#Airflow-Configuration)
- [DAG](#DAG)
- [Querying-Results](#querying-results)

# Requirements

AWS Account with Access Key and Secret Acces Key configured.
S3 Bucket for project's landing data already created. Athena database for querying data with name 'landing' created.

# EC2-Configuration

First step is create our EC2 instance with Amazon Linux in AWS (I recommend choosing a t2.large or higher for best Docker usage).

Then, connect to your VM through 'Connect' in EC2 options and run these commands:


### Update Linux<br>
```
sudo yum update
```

### Install Python and Pip<br>
```
sudo yum install pip
sudo yum install python3
```

### Install Docker<br>
```
sudo yum install docker -y
```

### Install Docker-Compose latest version<br>
```
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)"  -o /usr/local/bin/docker-compose
sudo mv /usr/local/bin/docker-compose /usr/bin/docker-compose
sudo chmod +x /usr/bin/docker-compose
```

### Once you have started the Docker service, you can verify that it is running by running the following command in your terminal:<br>

```
sudo systemctl start docker
sudo docker run hello-world
```

### To start the Docker service automatically when the instance starts, you can use the following command:<br>
```
sudo systemctl enable docker
```

## Airflow-Configuration<br>

### Download docker-compose.yaml from the airflow documentation<br>
```
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.8.1/docker-compose.yaml'
```
### Edit docker-compose to allow building requirements.txt<br>
vim docker-compose.yaml<br>

  comment these row (add # at the beginning)<br>
  ```
  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.8.1}
```
  
  uncomment that (remove # from the beginning)<br>
  ```
  #build: .
```
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
  
  save with !w and exit with !qa:

### Create airflow folders and env<br>
```
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

### Set Python libraries to install<br>
vim requirements.txt<br>
```
pandas
awswrangler
GoogleNews
boto3
```
save with :w! and exit with :qa!

### Set Dockerfile<br>
vim Dockerfile<br>
  ```
  FROM apache/airflow:2.8.1
  COPY requirements.txt  .
  RUN pip install -r "requirements.txt"
  ```
save with :w! and exit with :qa!


### Install Airflow<br>
```
sudo docker-compose up airflow-init
```

### Run Airflow<br>
```
sudo docker-compose up
```
![image](https://github.com/viniciusfjacinto/google-news-data-pipeline/assets/87664450/11dd38a6-5fac-45f6-bedc-a18e377b9078)


### Allowing access to Airflow UI<br>
Go to 'Security' menu in the EC2 console and alter 'Inbound Rules'. Choose 'Custom TCP rule' in the dropdown then you will be able to change the port to 8080.<br>

![image](https://github.com/viniciusfjacinto/google-news-data-pipeline/assets/87664450/9dd5d5bf-235e-4926-b961-8b55e22ad6ba)

Get VM's public url and then put ':8080' at the end of it. You should be able to access Airflow interface.<br>

For example, access link should be: <br>
```ec2-100-25-47-181.compute-1.amazonaws.com:8080```

Then you can log in Airflow using <br>
```
User: airflow 
Password: airflow
```

### Security
It's important that you create a new user with a more secure password after launching Airflow for the first time in EC2 oterwhise your machine and your data engineering infrastructure can be easily hacked.<br>
Go to Security > List Users and create a new Admin user and set 'airflow' user as inactive<br>
In this section you can also create other users with distinct permissions like Viewers for giving transparency to your data pipelines for stakeholders and other teams<br>

You can also create new users in the EC2 console using:
```
docker-compose run airflow-worker airflow users create --role Admin --username XXXXXXXX --email XXXXXXXX --firstname XXXXXXX --lastname XXXXXXXX --password XXXXXXXX
```

# Setting environment variables in Airflow

We will then get our AWS keys, the s3 bucket destination path and the terms we want GoogleNews to search and create them in section Admin > Variables <br><br>

![image](https://github.com/viniciusfjacinto/google-news-data-pipeline/assets/87664450/de5ccb84-b831-4a77-928a-e32ff41d978a)



# DAG

For creating and running our DAG we have to connect again to our EC2 throught 'Connect' and run these commands:

 ```
  cd dags
  vim gnews_dag.py
```
  copy the script text inside the file<br>

[gnews_dag.py](https://github.com/viniciusfjacinto/airflow-gnews-data-pipeline/blob/main/dags/gnews_dag.py)

save with :w! and exit with :qa!


Then our DAGs menu should look like this:

![image](https://github.com/viniciusfjacinto/google-news-data-pipeline/assets/87664450/ba9fcbfa-a78c-4b71-afb2-54f39887cdd4)


