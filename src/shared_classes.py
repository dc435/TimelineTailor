# ----------------------------------------
# A set of standard classes used across different repositories to ensure type consistency in API messages and Database:
# ----------------------------------------



from pydantic import BaseModel
import enum
from datetime import date

class JobStatus(enum.Enum):
    CREATED = 1
    PROCESSING = 2
    COMPLETE = 3
    ERROR = 4

class NewJob(BaseModel):
    jobid: str
    name: str
    original_text: str
    client_address: str
    
class Snippet(BaseModel):
    pre: str = ""
    mid: str = ""
    post: str = ""

class Result(BaseModel):
    id: str = ""
    parsed: bool = False
    date_text: str = ""
    description: str = ""
    snippets: list[Snippet] = [Snippet()]
    length: str = ""
    date_formatted: date = date(9999,12,31)

class BasicReply(BaseModel):
    success: bool
    msg: str

class Update(BaseModel):
    job_done: bool
    processing_error: bool
    user_update: str

class SendUpdate(BaseModel):
    jobid: str
    status: JobStatus
    user_update: str

class DateFormat(enum.Enum):
    UNKNOWN = 1
    Y = 2
    MY = 3
    DMY = 4

class ModelEvent(BaseModel):
    
    jobid: str = ""
    ent_text: str = ""    
    description: str = ""
    date_success: bool = False
    date_formatted: date = date.today()
    date_format: DateFormat = DateFormat.UNKNOWN
    context_left: str = ""
    context_right: str = ""
    delimiter: str = ""

class ModelOutput(BaseModel):
    success: bool
    message: str
    events: list[ModelEvent]

