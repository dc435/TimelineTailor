# ----------------------------------------
# Methods for original database build, and database objects
# Using SQLalchemy
# ----------------------------------------



from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from shared_classes import JobStatus, DateFormat

Base  = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    jobid  = Column(String, primary_key=True)
    name = Column(String)
    text = Column(String)
    status = Column(Enum(JobStatus))
    user_update = Column(String)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    client_address = Column(String)
    events = relationship('Event', backref='job')

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, index=True)
    jobid = Column(String, ForeignKey('jobs.jobid'))
    ent_text = Column(String)    
    description = Column(String)
    date_success = Column(Boolean)
    date_formatted = Column(DateTime)
    date_format = Column(Enum(DateFormat))
    context_left = Column(String)
    context_right = Column(String)
    delimiter = Column(String)

def build_db(engine):

    Base.metadata.create_all(engine)
