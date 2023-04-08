# ----------------------------------------
# Configuration set-up
# Two config settings are used: 1) Deployment in docker; 2) Running locally through IDE
# ----------------------------------------



import os
from logging import Logger
import boto3
import json

class Config:

    STD_ERROR_MESSAGE = "We encountered an error. Our apologies. Please try again later."
    STD_SUCCESS_MESSAGE = "Success."

    def __init__(self):
        self.MSG = ""

class DockerConfig(Config):

    def __init__(self):

        self.FRONTEND_HOST = "0.0.0.0" 
        self.FRONTEND_PORT = 80
        self.TEMPLATES_DIR = "../app/templates"
        self.BASE_HREF = os.environ.get("BASE_HREF")

        aws_region=os.environ.get('AWS_REGION')
        db_secret_name=os.environ.get('DB_SECRET_NAME')
        model_secret_name=os.environ.get('MODEL_SECRET_NAME')

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=aws_region
        )

        db_response = client.get_secret_value(SecretId=db_secret_name)
        db_details = json.loads(db_response['SecretString'])
        model_response = client.get_secret_value(SecretId=model_secret_name)
        model_details = json.loads(model_response['SecretString'])
        
        self.DB_DRIVERNAME="postgresql+psycopg2"
        self.DB_USERNAME= db_details['username']
        self.DB_HOST = db_details['host']
        self.DB_PORT = db_details['port']
        self.DB_DATABASE = db_details['dbname']
        self.DB_PASSWORD = db_details['password']

        self.MODEL_API = model_details['model_api']
        self.MODEL_KEY = model_details['model_key']

        self.LOCAL_CONFIG = False

class LocalConfig(Config):

    def __init__(self):

        self.FRONTEND_HOST = "localhost"
        self.FRONTEND_PORT = 8000
        self.TEMPLATES_DIR = os.getcwd() + "/src/templates/" 
        self.BASE_HREF = "http://localhost:8000"

        self.DB_DRIVERNAME="postgresql+psycopg2"
        self.DB_USERNAME="postgres"
        self.DB_HOST="localhost"
        self.DB_PORT="5432"
        self.DB_DATABASE="timeline_1"
        self.DB_PASSWORD=input("Enter DB password:")
        # self.MODEL_API=input("Enter Model API:") # If using remote model
        # self.MODEL_KEY=input("Enter Model Key:") # If using remote model
        self.MODEL_API="x"
        self.MODEL_KEY="x"
        self.LOCAL_CONFIG = True

def get_config(log: Logger):
    if os.environ.get('IN_DOCKER') is not None:
        log.info("Docker Environment Selected.")
        return DockerConfig()
    else:
        log.info("Local Environment Selected.")
        return LocalConfig()
