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

Then, connect to your VM and run these commands:

