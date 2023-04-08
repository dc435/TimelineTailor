# ----------------------------------------
# Methods for interacting with database
# ----------------------------------------


from sqlalchemy.engine import Engine
from shared_classes import NewJob, JobStatus, Update
from db import Event

# Create new job
def db_create_new_job(
        engine: Engine, 
        newjob: NewJob
    ):

    from sqlalchemy.orm import sessionmaker
    from db import JobStatus
    from db import Job

    INITIAL_UPDATE_TEXT = "New job '" + newjob.name + "' created."
    
    job = Job(
        jobid=newjob.jobid,
        name=newjob.name,
        text=newjob.original_text,
        status=JobStatus.CREATED,
        user_update=INITIAL_UPDATE_TEXT,
        client_address=newjob.client_address
    )

    Session = sessionmaker(bind=engine)
    with Session() as session:
        session.add(job)
        session.commit()

# Get job update (eg. 'PROCESSING', 'COMPLETE' etc)
def db_get_job_update(
        engine: Engine, 
        jobid: str
    ) -> Update:

    from sqlalchemy.orm import sessionmaker
    from db import Job
    from db import JobStatus
    from shared_classes import Update

    Session = sessionmaker(bind=engine)
    with Session() as session:

        job_done = False
        processing_error = False
        query = session.query(Job)
        job = query.filter(Job.jobid == jobid).first()
        if job.status == JobStatus.COMPLETE:
            job_done = True
        if job.status == JobStatus.ERROR:
            processing_error = True
        return Update(job_done=job_done,processing_error=processing_error,user_update=job.user_update)

# Add events to job. Called when events list is returned from model:
def db_add_new_events(engine: Engine, events: list[Event]):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    with Session() as session:
        for e in events:
            session.add(e)
        session.commit()

# Get events from job. Called prior to displaying /results.html page:
def db_get_events(
        engine: Engine, 
        jobid: str
    ) -> list[Event]:

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    with Session() as session:
        query = session.query(Event)
        events = query.filter(Event.jobid == jobid).all()
        return events
    
# Get job jupdate. Called periodically to provide user update when 'processing' page is displayed:
def db_update_job(engine: Engine, jobid: str, status:JobStatus, user_update:str):
    from sqlalchemy.orm import sessionmaker
    from db import Job
    Session = sessionmaker(bind=engine)
    with Session() as session:
        query = session.query(Job)
        job = query.filter(Job.jobid == jobid).first()
        job.status = status
        job.user_update = user_update
        session.commit()

# Helper methods:
def db_get_job_status(engine: Engine, jobid: str) -> JobStatus:
    from sqlalchemy.orm import sessionmaker
    from db import Job
    Session = sessionmaker(bind=engine)
    with Session() as session:
        query = session.query(Job)
        job = query.filter(Job.jobid == jobid).first()
        return job.status

def db_get_job_name(engine: Engine, jobid: str) -> str:
    from sqlalchemy.orm import sessionmaker
    from db import Job
    Session = sessionmaker(bind=engine)
    with Session() as session:
        query = session.query(Job)
        job = query.filter(Job.jobid == jobid).first()
        return job.name