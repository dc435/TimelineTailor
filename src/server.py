# --------------------------------------------

# TIMELINETAILOR.COM - server.py

# This is the entry point for TimelineTailor. 
# It is a front-end API which serves html Jinja templates
# It calls other functions from 'job_processing', 'db_api' and 'model_api' to conduct text processing

# --------------------------------------------

# Imports
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from starlette.templating import Jinja2Templates
import uvicorn
import hashlib
from requests.exceptions import ConnectionError
from shared_classes import NewJob
from job_processing import start_newjob
from sqlalchemy.exc import OperationalError

# Initialise log:
import logger
log = logger.get_logger()

# Get configurations:
# Config will either be online or local, depending on execution environment:
from config import get_config
config = get_config(log)
frontend_host = config.FRONTEND_HOST
frontend_port = config.FRONTEND_PORT
templates_dir = config.TEMPLATES_DIR
base_href = config.BASE_HREF
local_config = config.LOCAL_CONFIG
std_error_message = config.STD_ERROR_MESSAGE
std_success_message = config.STD_SUCCESS_MESSAGE
db_drivername = config.DB_DRIVERNAME
db_username = config.DB_USERNAME
db_host = config.DB_HOST
db_port = config.DB_PORT
db_database = config.DB_DATABASE
db_password = config.DB_PASSWORD
model_api = config.MODEL_API
model_key = config.MODEL_KEY

# Connect to DB
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from db import build_db
url = URL.create(
    drivername=db_drivername,
    username=db_username,
    password=db_password,
    host=db_host,
    port=db_port,
    database=db_database
)
try:
    engine = create_engine(url)
    build_db(engine)
    log.info("Successfully connected to DB")
except OperationalError:
    log.critical("Failed to connect to database.", exc_info=1)

# Start FastAPI app:
app = FastAPI()
templates = Jinja2Templates(directory=templates_dir)

# Cross-origin resource sharing configuration:
origins = [
    "https://timelinetailor.com",
    "https://www.timelinetailor.com",
    "https://timelinetailor.com/home",
    "https://www.timelinetailor.com/home",
    "http://timelinetailor.com",
    "http://www.timelinetailor.com",
    "http://timelinetailor.com/home",
    "http://www.timelinetailor.com/home",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
#  API: Home Page:
# =====================
@app.get("/")
@app.get("/home/")
def home(request: Request):
    log.info("'/' called from: " + str(request.client))
    print(templates_dir)
    return templates.TemplateResponse("index.html", {"request": request, "base_href": base_href})

# =====================
#  API: New job:
# =====================
@app.post('/new_job/')
def new_job(
        request: Request,
        user_input: dict,
        background_tasks: BackgroundTasks
    ) -> dict:

    log.info("'/new_job/' called from: " + str(request.client))

    # Set default return values:
    success = False
    url = "/"
    message = "Our apologies. There was an error during processing. Please try again later."

    try:

        text = user_input['text'][:500000]
        name = user_input['jobname'] if user_input['jobname'] != "" else text[:30]
        jobid = hashlib.sha1(bytes(text, 'utf-8')).hexdigest()

        newjob = NewJob(
            jobid=jobid,
            name=name,
            original_text=text,
            client_address=str(request.headers.get('X-Forwarded-For'))
        )

        success = True
        url = "/processing/" + jobid
        message = ""

        background_tasks.add_task(start_newjob, newjob, log, background_tasks, engine, model_api, model_key, local_config, std_error_message, std_success_message)

    except:

        log.error("Could not process new job.", exc_info=True)

    finally:

        return {"success": success, "url": url, "message": message}

# =====================
#  API: Processing Page:
# =====================
@app.get("/processing/{jobid}")
def processing(request: Request, jobid: str):
    log.info("'/processing/' called from: " + str(request.client))
    resultsurl = base_href + "/results/" + jobid
    return templates.TemplateResponse("processing.html", {"request": request, "jobid":jobid, "update_interval": 5000, "resultsurl":resultsurl, "base_href": base_href})


# =====================
#  API: Get Update dict:
# =====================
@app.get("/get_update/{jobid}")
def get_update(
        request:Request, 
        jobid:str
    ) -> dict:
    
    log.info("'/get_update/" + jobid + "' called from: " + str(request.client))

    done = False
    error = True
    message = "Our apologies. We have encountered an error. Please try again later."

    try:

        from job_processing import get_job_update
        update = get_job_update(jobid, log, std_error_message, engine)
        if update.job_done:
            done = True
        if not update.processing_error:
            error = False
        message = update.user_update

    except ConnectionError:

        log.error("BACKEND OFFLINE. Could not get job update. Job: " + jobid)

    except:

        log.error("Could not get job update. Job: " + jobid)

    finally:

        return {'done':done,'error':error,'message':message}
        

# =====================
#  API: Results Page:
# =====================
@app.get("/results/{jobid}")
def results(request: Request, jobid: str):
    
    log.info("'/get_results/" + jobid + "' called from: " + str(request.client))

    from shared_classes import Result
    results = [Result().json()]
    jobname = ""
    
    try:

        from job_processing import get_results, get_job_name
        results = get_results(jobid, engine, log)
        jobname = get_job_name(jobid, engine, log)

    except ConnectionError:
    
        log.error("BACKEND OFFLINE. Could not get results. Job: " + jobid)

    except:

        log.error("Could not get results. Job: " + jobid)

    finally:

        return templates.TemplateResponse("results.html", {"request": request, "jobid":jobid, "results":results, "jobname":jobname, "base_href": base_href})

# =====================
#  API: About Page:
# =====================
@app.get("/about/")
def about(request: Request):
    log.info("'/about/' called from: " + str(request.client))
    return templates.TemplateResponse("about.html", {"request": request, "base_href": base_href})

# =====================
#  API: Help Page:
# =====================
@app.get("/help/")
def about(request: Request):
    log.info("'/help/' called from: " + str(request.client))
    return templates.TemplateResponse("help.html", {"request": request, "base_href": base_href})


# =====================
#  RUN SERVER:
# =====================
if __name__ == '__main__': 
    uvicorn.run(app, host=frontend_host,port=frontend_port)