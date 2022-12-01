#!/bin/bash

echo "Script for preparing the development environment"
echo "------------------------------------------------"

echo "Checking if config.ini exists in the current working dir -->"
if test -f "config.ini"; then
    echo "exists"
else
        echo "Could not locate config.ini file"
        exit 1; fi
echo "------------------------------------------------"

echo "Checking if log_worker.yaml exists in the current working dir -->"
if test -f "log_worker.yaml"; then
    echo "exists"
else
        echo "Copying log config file from local dev template log_worker.yaml.dev"
        cp log_worker.yaml.dev log_worker.yaml
        if [ $? -eq 0 ]; then echo "OK"; else echo "No template log_worker.yaml file to copy"; exit 1; fi
fi
echo "------------------------------------------------"

echo "Checking if log_migrate_db.yaml exists in the current working dir -->"
if test -f "log_migrate_db.yaml"; then
    echo "exists"
else
        echo "Copying log config file from local dev template log_migrate_db.yaml.dev"
        cp log_migrate_db.yaml.dev log_migrate_db.yaml
        if [ $? -eq 0 ]; then echo "OK"; else echo "Problem copying log_migrate_db.yaml file"; exit 1; fi
fi
echo "------------------------------------------------"

echo "Getting python3 executable location"
python_exec_loc=$(which python3)
if [ $? -eq 0 ]; then echo "OK"; else echo "Problem getting python3 exec location"; exit 1; fi
echo "$python_exec_loc"
echo "------------------------------------------------"

echo "Running DB migrations"
$python_exec_loc migrate_db.py
if [ $? -eq 0 ]; then echo "OK"; else echo "DB migration FAILED"; exit 1; fi
echo "------------------------------------------------"

echo "Running database migration file test"
$python_exec_loc test_migrate_db.py
if [ $? -eq 0 ]; then echo "OK"; else echo "Project test FAILED"; exit 1; fi
echo "------------------------------------------------"


echo "All clear! Everything is ready to go"
echo "to start the program, execute:"
echo "$python_exec_loc worker_2_db.py"
