Public ip address: 52.27.4.77

To log in to the VM: ssh -i ~/.ssh/udacity_key.rsa root@52.27.4.77
To see the webpage: visit 52.27.4.77:80 in your browser

# Item catalog app

## Introduction
This application allows users to create categories and place items in those categories. Only signed in users can create, update and delete items and categories, and they can only manage their own categories and items.

## Requirements
Flask == 0.10.1
SQLAlchemy == 0.8.4
httplib2 == 0.9.1
dicttoxml == 1.6.6

## Set Up Environment & Installation
- setup the environment: ```pip install -r requirements.txt```
- setup the database: ```python database_setup.py```
- start the server: ```python project.py```
- visit http://localhost:3000 to see the project running

## Usage
When the user is logged in, the user will have the option to create, update and delete categories and items.

## Resources
- the styling is copied from Udacity's oauth project.
