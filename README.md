# Greenline Tracker

## Overview

Greenline Tracker is a web application that allows users to track the status of trains on the Green Line, view schedules, and manage travel groups. This README provides instructions for setting up and running the project locally.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Using requirements.txt](#using-requirementstxt)
- [Creating an .env file](#creating-an-env-file)
- [Running the Application](#running-the-application)
- [Using the Dump FIle](#using-the-dump-file)
- [Technologies Used](#technologies-used)

## Prerequisites

Before you begin, ensure you have the following software installed on your machine:

1. **Python 3.8 or higher**
  - Download from: [Python Downloads](https://www.python.org/downloads/)

2. **pip (Python package installer)**
  - pip is included with Python installations. You can check if it's installed by running `pip --version` in your terminal.

3. **MySQL**
  - Download from: [MySQL Downloads](https://dev.mysql.com/downloads/)

4. **Git**
  - Download from: [Git Downloads](https://git-scm.com/downloads)

## Using requirements.txt

The `requirements.txt` file contains a list of all the Python libraries your project depends on. To install these libraries, use the following command:

```bash
pip install -r requirements.txt
```

## Creating an .env file
An .env file is used to store environment variables for your application. These variables can include sensitive information such as API keys and database credentials.

Create an .env file in the root directory of your project:
```bash
touch .env
```

Open the .env file in a text editor and add the following lines:
```bash
MBTA_API_KEY=c671369fcd2846b88f782851472f2c7b
MBTA_BASE_URL=https://api-v3.mbta.com
SQLALCHEMY_DATABASE_URI=mysql+pymysql://<user>:<passwd>@localhost/mbta_tracker
SECRET_KEY=PranavAndMithunsProject
```
Replace < user > and < passwd > to match your credentials to connect the DB successfully.

## Using the dump file

In the Resources `DB_Dump` folder there is a single dump file that contains all the code required to set up the DB. Double clicking on the file will open it in MySQL Workbench. Run the file and verify that the tables have been updated

## Running the Application

Navigate to the directory with the `app.py` file. This can be done by opening the `Code` folder in the provided zip file. Then open the terminal in that path and run the below command.

```
python -m flask run
```

## Technologies Used

1. Flask: A lightweight WSGI web application framework.
2. Flask-SQLAlchemy: An extension for Flask that adds support for SQLAlchemy.
3. MySQL: The database used to store application data.
4. Requests: A simple HTTP library for Python to make API calls.
5. dotenv: A library to load environment variables from a .env file.
