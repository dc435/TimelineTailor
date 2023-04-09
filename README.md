# TimelineTailor

An event extraction and timeline building website, written in Python. Currently deployed at [Timeline Tailor](www.timelinetailor.com).

Timeline Tailor is a personal demonstration project to illustrate the author's skills in software design, natural language processing and deployment. Feel free to adopt the code base, or reach out if you have any queries.


# Overview

This repository is the codebase for the frontend website presently deployed at www.timelinetailor.com.

The app takes unstructured English-language text (up to 500,000 characters) are returns a timeline / chronological summary of the events described therein. The code in this repo:

1. Serves the fronted;
2. Coordinates messaging between the text-processing model, the database and the user.

The substantive text-processing model is hosted on a separate repository.


# User Experience

## Home screen

The user can paste any unstructured English text into the home screen text-box. A limit of 500,000 characters is imposed. 

![homescreen](/src/img/homescreen.png)


## Processing

Each job is given a unique job ID, being the hash of the raw text. JobID, creation time, text and other information is stored in a database for that job ID. When the model has completed processing, all event objects (being the date-event pairs) are stored against that Job ID.


## Results

Results are displayed in a html accordian element. Events with the same date and similar descriptions are grouped together. A 'snippet' of the original text context is also displayed.

![results](/src/img/results.png)



# Languages & Packages

Several packages are deployed, including:

- HTML: Jinja2 html templates with Bootstrap library and custom Javascript
- Server and API: Uvicorn, FastAPI
- Container: Docker
- Type checking: Pydantic
- Database: SQLAlchemy, with postgres


