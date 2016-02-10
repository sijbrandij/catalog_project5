# Setup

## Basic configuration

### Launch VM with Udacity account
Public IP: ```52.27.4.77```

Login to VM: ```ssh grader@52.27.4.77 -p 2200 -i ~/.ssh/grader```
The ssh key for user grader was created with the password 'grader'
It may also be necessary to change permissions on the ssh key file:
```chmod 600 ~/path/to/keyfile```

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
Edit ```/etc/ssh/sshd_config```:
```
# What ports, IPs and protocols we listen for
Port 22
```
Change port number to 2200 (assignment) and restart server
```
sudo service ssh restart
```

Source: https://help.ubuntu.com/community/SSH/OpenSSH/Configuring


### Confire UFW to only allow incoming connections for SSH (2200), HTTP (80) and NTP (123)
```
sudo ufw default deny outgoing
sudo ufw allow http
sudo ufw allow ntp
sudo ufw allow 2200
sudo ufw enable
```

## Install application

### Install and configure Apache to serve a Python mod_wsgi application
### Install and configure PostgreSQL
```
sudo apt-get install postgresql postgresql-contrib
```

#### Do not allow remote connections
PostgreSQL does not allow remote connections by default (source https://www.digitalocean.com/community/tutorials/how-to-secure-postgresql-on-an-ubuntu-vps)

#### Create a new user named 'catalog' with limited permissions
```createuser --interactive```
answer 'no' to all of the questions
password of catalog user is 'catalog'

### Install git, clone and setup your Catalog app project to be served .git directory should not be visible to the browser
```
sudo apt-get install git
git clone https://github.com/sijbrandij/catalog_project5.git
```

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
- start the server: ```python __init__.py```
- visit http://localhost:3000 to see the project running

## Usage
When the user is logged in, the user will have the option to create, update and delete categories and items.

## Resources
- the styling is copied from Udacity's oauth project.
