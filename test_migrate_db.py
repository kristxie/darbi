import os
import requests
import mysql.connector

print("Database migration file test")

# Testing if database migration file exists on disk in the current working directory
print("----------")
print("Checking if database migration  file exists -->")
assert os.path.isfile("migrate_db.py") == True
print("OK")
print("----------")
