# google-news-data-pipeline
A simple coded data pipeline to transfer data from Google News to Amazon S3 while creating a data lake for refining information between layers. All project is built using Apache Airflow and Amazon EC2.
The project is divided into three steps which involve mounting and configuring EC2 to initialize Airflow, and running the Python script in the cloud to store the results in a bucket

## Table of Contents

- [Installing Airflow on EC2](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installing Airflow on EC2

First step is create our EC2 instance with Amazon Linux in AWS (I recommend choosing an t2.large or higher for best Docker usage).

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

### Airflow Steps:<br>

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
  FROM apache/airflow:2.7.0
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


