# ----------------------------------------
# Main set of methods for job processing
# The methods coordinate calls to database and to model
# ----------------------------------------



from shared_classes import NewJob, Update, Result
from logging import Logger
from fastapi import BackgroundTasks
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, OperationalError
from config import LocalConfig


# =====================
# Start new job:
# 1. Add new job to DB
# 2. Send new job to model
# =====================
def start_newjob(
        newjob: NewJob,
        log: Logger,
        background_tasks: BackgroundTasks,
        engine: Engine,
        model_api: str,
        model_key: str,
        model_url: str,
        local_config: LocalConfig,
        std_error_message: str,
        std_success_message: str
    ):

    log.info("'start_newjob called'. JobId: " + newjob.jobid)

    # Imports:
    from db_api import db_create_new_job

    # Try to add new job to DB. Then send to model for processing:
    try:

        db_create_new_job(engine, newjob)
        log.info("Created new job in DB. JobId: " + newjob.jobid)
        background_tasks.add_task(send_to_model, newjob, log, engine, model_api, model_key, local_config, std_error_message, std_success_message)

    # Exception if job already exists on DB:
    except IntegrityError:

        try:

            from db_api import db_get_job_status, db_update_job
            from shared_classes import JobStatus
            status = db_get_job_status(engine,newjob.jobid)
            if status == JobStatus.COMPLETE or status == JobStatus.PROCESSING:
                log.info("Incoming job already complete / processing. JobId: " + newjob.jobid)
            if status == JobStatus.ERROR or status == JobStatus.CREATED:
                db_update_job(engine,newjob.jobid,JobStatus.PROCESSING,user_update="Processing Job.")
                background_tasks.add_task(send_to_model, newjob, log, engine, model_api, model_key, model_url, local_config, std_error_message, std_success_message)
                log.info("Changed job status from Error/Created to 'PROCESSING'. Send job to process queue. Job: " + newjob.jobid)

        except: # Exception for DB connection:

            log.exception("Could not query / amend status of existing job. JobId: " + newjob.jobid)

    except OperationalError: # Exception for DB connection:

        log.exception("DATABASE OFFLINE. Could not create new job in DB. JobId: " + newjob.jobid)

    except Exception:

        log.exception("Could not create new job in DB. JobId: " + newjob.jobid)



# =====================
# Send job to model:
# =====================
def send_to_model(
        newjob: NewJob,
        log: Logger,
        engine: Engine,
        model_api: str,
        model_key: str,
        model_url: str,
        local_config: LocalConfig,
        std_error_message: str,
        std_success_message: str
    ):

    log.info("'send_to_model called'. JobId: " + newjob.jobid)

    from model_api import model_process_job
    from shared_classes import JobStatus
    from db_api import db_update_job
    from requests.exceptions import ConnectionError

    status = JobStatus.PROCESSING

    # Update job status and user update on DB (=Job being sent to model for processing):
    from sqlalchemy.exc import OperationalError
    num_lines = len(newjob.original_text.splitlines())
    user_update = "Job '" + newjob.name + "' (" + str(num_lines) + " lines), is being processed."
    try:
        db_update_job(engine=engine, jobid=newjob.jobid, status=status, user_update=user_update)
    except OperationalError:
        log.exception("DATABASE OFFLINE. Could not update DB model user update to: " + user_update + ". Job:" + newjob.jobid)
    except:
        log.exception("Could not update DB model user update to: " + user_update + ". Job:" + newjob.jobid)

    # Send to model for processing:
    try:
        events = model_process_job(model_api, model_key, model_url, newjob, log, local_config)
        log.info("Job processed by model. " + str(len(events)) + " events returned to send_to_model. Job: " + newjob.jobid)
    except ConnectionError:
        status = JobStatus.ERROR
        log.exception("MODEL OFFLINE. Model could not process job. Job: " + newjob.jobid)
    except:
        status = JobStatus.ERROR
        log.exception("Model could not process job. Job: " + newjob.jobid)

    if status != JobStatus.ERROR:

        from db_api import db_add_new_events
        try:
            db_add_new_events(engine, events)
            status = JobStatus.COMPLETE
            log.info("Events added to DB. Job: " + newjob.jobid)
        except OperationalError:
            status = JobStatus.ERROR
            log.exception("DATABASE OFFLINE. Could not add recently processed events to DB. Job:" + newjob.jobid)
        except:
            status = JobStatus.ERROR
            log.exception("Could not add recently processed events to DB. Job:" + newjob.jobid)

    user_update = std_error_message if status == JobStatus.ERROR else std_success_message

    try:
        db_update_job(engine=engine, jobid=newjob.jobid, status=status, user_update=user_update)
        log.info("Update DB model status to: " + str(status) + ". Job:" + newjob.jobid)
    except OperationalError:
        log.exception("DATABASE OFFLINE. Could not update DB model status to:" + str(status) + ". Job:" + newjob.jobid)
    except:
        log.exception("Could not update DB model status to:" + str(status) + ". Job:" + newjob.jobid)


# =====================
# Get job update:
# =====================
def get_job_update(
        jobid:str,
        log: Logger,
        std_error_message: str,
        engine: Engine
    ) -> Update:

    # Default return values:
    update = Update(job_done = False, processing_error=True, user_update=std_error_message)

    try:
        from db_api import db_get_job_update
        update = db_get_job_update(engine,jobid)

    except OperationalError:

        log.exception("DATABASE OFFLINE. Could not get job update. Job:" + jobid)

    except Exception:

        log.exception("Could not get job update. Job:" + jobid)

    finally:

        return update

# =====================
#  Get job results:
# =====================
def get_results(
        jobid:str,
        engine: Engine,
        log: Logger
    ) -> list[Result]:

    results = [Result()]

    try:

        from db_api import db_get_events
        events = db_get_events(engine, jobid)
        from post_processing import get_results
        results = get_results(events)

    except OperationalError:

        log.exception("DATABASE OFFLINE. Could not get results. Job:" + jobid)

    except Exception:

        log.exception("Could not get results. Job:" + jobid)

    finally:

        return results

# =====================
#  Get job name:
# =====================
def get_job_name(
        jobid:str,
        engine: Engine,
        log: Logger
    ) -> dict:

    # Default return values:
    reply = ""

    try:
        from db_api import db_get_job_name
        reply = db_get_job_name(engine,jobid)

    except OperationalError:

        log.exception("DATABASE OFFLINE. Could not get job name. Job:" + jobid)

    except Exception:

        log.exception("Could not get job name. Job:" + jobid)

    finally:

        return reply