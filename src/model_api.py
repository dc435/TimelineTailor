# ----------------------------------------
# Methods for calling the text processing model
# Model is hosted on banana serverless-GPU
# ----------------------------------------



# import banana_dev as banana
from banana_dev import Client
from shared_classes import NewJob, ModelOutput
from db import Event
import json
from logging import Logger

def model_process_job(
        api_key: str,
        model_key: str,
        model_url: str,
        newjob: NewJob,
        log: Logger,
        local_config: bool
    ) -> list[Event]:

    if local_config:

        url = "http://localhost:8002/"

        import requests
        response = requests.post(url, newjob.json())
        modelOutput = json.loads(response.json())
        modelOutput = ModelOutput(**modelOutput)
        events = []
        if modelOutput.success:
            for e in modelOutput.events:
                event = Event(**e.dict())
                events.append(event)
        else:
            log.error("Model failed to process newjob. Error msg: " + modelOutput.message)

    else:

        model_input = newjob.dict()

        my_model = Client(url=model_url, api_key=api_key)
        response, meta = my_model.call("/",model_input)
        # response = banana.run(api_key, model_key, model_input)
        # modelOutput = json.loads(response['modelOutputs'][0])
        # modelOutput = ModelOutput(**modelOutput)
        modelOutput = ModelOutput(**response)
        events = []
        if modelOutput.success:
            for e in modelOutput.events:
                event = Event(**e.dict())
                events.append(event)
        else:
            log.error("Banana API failed to process newjob. Error msg: " + modelOutput.message)
            raise ConnectionError

    return events
