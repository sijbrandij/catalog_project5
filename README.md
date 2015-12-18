# Setup

## Basic configuration

### Launch VM with Udacity account
Public IP: ```52.27.4.77```
Login to VM: ```ssh -i ~/.ssh/udacity_key.rsa root@52.27.4.77```

### Create user named grader and give sudo rights
```
adduser grader
```
To give the user sudo rights, add a file called 'grader' to /etc/sudoers.d (Files are picked up by /etc/sudoers file). Contents of the file:
```
grader ALL=(ALL) NOPASSWD:ALL
```

### Update all currently installed packages
```
sudo apt-get update
sudo apt-get upgrade
```

### Configure local timezone to UTC
```
sudo dpkg-reconfigure tzdata
```
Scroll down to 'etc' and select 'UTC' in second list.
Source: http://askubuntu.com/questions/138423/how-do-i-change-my-timezone-to-utc-gmt

## Secure your server

### Change SSH port from 22 to 2200
### Confire UFW to only allow incoming connections for SSH (2200), HTTP (80) and NTP (123)

## Install application

### Install and configure Apache to serve a Python mod_wsgi application
### Install and configure PostgreSQL
#### Do not allow remote connections
#### Create a new user named 'catalog' with limited permissions
### Install git, clone and setup your Catalog app project to be served .git directory should not be visible to the browser
### Configure third party authentication


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
