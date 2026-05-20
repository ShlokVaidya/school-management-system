# config.py
# This file stores all database connection settings
# Change the values below to match your MySQL setup

# MySQL database connection details
MYSQL_HOST = 'localhost'       # usually localhost
MYSQL_USER = 'root'            # your MySQL username
MYSQL_PASSWORD = '!sentry!'            # your MySQL password (empty if none set)
MYSQL_DB = 'student_tracker'   # the database name we created

# Secret key for session (can be anything, just keep it secret)
SECRET_KEY = 'student_database_management_key'
