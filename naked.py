import requests
import json
import datetime
import time
import yaml
import logging
import logging.config
import mysql.connector

from datetime import datetime
from configparser import ConfigParser
from mysql.connector import Error

# Loading logging configuration
with open('./log_worker.yaml', 'r') as stream:
        log_config = yaml.safe_load(stream)

logging.config.dictConfig(log_config)

# Creating logger
logger = logging.getLogger('root')


logger.info('Asteroid processing service')

# Initiating and reading config values
logger.info('Loading configuration from file')

try:
	config = ConfigParser()
	config.read('config.ini')

	nasa_api_key = config.get('nasa', 'api_key')
	nasa_api_url = config.get('nasa', 'api_url')

	mysql_config_mysql_host = config.get('mysql_config', 'mysql_host')
	mysql_config_mysql_db = config.get('mysql_config', 'mysql_db')
	mysql_config_mysql_user = config.get('mysql_config', 'mysql_user')
	mysql_config_mysql_pass = config.get('mysql_config', 'mysql_pass')

except:
	logger.exception('')
logger.info('DONE')

def init_db():
	global connection
	connection = mysql.connector.connect(host=mysql_config_mysql_host, database=mysql_config_mysql_db, user=mysql_config_mysql_user, password=mysql_config_mysql_pass)

def get_cursor():
	global connection
	try:
		connection.ping(reconnect=True, attempts=1, delay=0)
		connection.commit()
	except mysql.connector.Error as err:
		logger.error("No connection to db " + str(err))
		connection = init_db()
		connection.commit()
	return connection.cursor()

# Check if asteroid exists in db
def mysql_check_if_ast_exists_in_db(request_day, ast_id):
	records = []
	cursor = get_cursor()
	try:
		cursor = connection.cursor()
		result  = cursor.execute("SELECT count(*) FROM ast_daily WHERE `create_date` = '" + str(request_day) + "' AND `ast_id` = '" + str(ast_id) + "'")
		records = cursor.fetchall()
		connection.commit()
	except Error as e :
		logger.error("SELECT count(*) FROM ast_daily WHERE `create_date` = '" + str(request_day) + "' AND `ast_id` = '" + str(ast_id) + "'")
		logger.error('Problem checking if asteroid exists: ' + str(e))
		pass
	return records[0][0]

# Asteroid value insert
def mysql_insert_ast_into_db(create_date, hazardous, name, url, diam_min, diam_max, ts, dt_utc, dt_local, speed, distance, ast_id):
	cursor = get_cursor()
	try:
		cursor = connection.cursor()
		result  = cursor.execute( "INSERT INTO `ast_daily` (`create_date`, `hazardous`, `name`, `url`, `diam_min`, `diam_max`, `ts`, `dt_utc`, `dt_local`, `speed`, `distance`, `ast_id`) VALUES ('" + str(create_date) + "', '" + str(hazardous) + "', '" + str(name) + "', '" + str(url) + "', '" + str(diam_min) + "', '" + str(diam_max) + "', '" + str(ts) + "', '" + str(dt_utc) + "', '" + str(dt_local) + "', '" + str(speed) + "', '" + str(distance) + "', '" + str(ast_id) + "')")
		connection.commit()
	except Error as e :
		logger.error( "INSERT INTO `ast_daily` (`create_date`, `hazardous`, `name`, `url`, `diam_min`, `diam_max`, `ts`, `dt_utc`, `dt_local`, `speed`, `distance`, `ast_id`) VALUES ('" + str(create_date) + "', '" + str(hazardous) + "', '" + str(name) + "', '" + str(url) + "', '" + str(diam_min) + "', '" + str(diam_max) + "', '" + str(ts) + "', '" + str(dt_utc) + "', '" + str(dt_local) + "', '" + str(speed) + "', '" + str(distance) + "', '" + str(ast_id) + "')")
		logger.error('Problem inserting asteroid values into DB: ' + str(e))
		pass

def push_asteroids_arrays_to_db(request_day, ast_array, hazardous):
	for asteroid in ast_array:
		if mysql_check_if_ast_exists_in_db(request_day, asteroid[9]) == 0:
			logger.debug("Asteroid NOT in db")
			mysql_insert_ast_into_db(request_day, hazardous, asteroid[0], asteroid[1], asteroid[2], asteroid[3], asteroid[4], asteroid[5], asteroid[6], asteroid[7], asteroid[8], asteroid[9])
		else:
			logger.debug("Asteroid already IN DB")

if __name__ == "__main__":

	connection = None
	connected = False

	init_db()

	# Opening connection to mysql DB
	logger.info('Connecting to MySQL DB')
	try:
		# connection = mysql.connector.connect(host=mysql_config_mysql_host, database=mysql_config_mysql_db, user=mysql_config_mysql_user, password=mysql_config_mysql_pass)
		cursor = get_cursor()
		if connection.is_connected():
			db_Info = connection.get_server_info()
			logger.info('Connected to MySQL database. MySQL Server version on ' + str(db_Info))
			cursor = connection.cursor()
			cursor.execute("select database();")
			record = cursor.fetchone()
			logger.debug('Your connected to - ' + str(record))
			connection.commit()
	except Error as e :
		logger.error('Error while connecting to MySQL' + str(e))

	# Getting todays date
	dt = datetime.now()
	request_date = str(dt.year) + "-" + str(dt.month).zfill(2) + "-" + str(dt.day).zfill(2)  
	logger.debug("Generated today's date: " + str(request_date))

	# Requesting INFO from NASA API
	logger.debug("Request url: " + str(nasa_api_url + "rest/v1/feed?start_date=" + request_date + "&end_date=" + request_date + "&api_key=" + nasa_api_key))
	r = requests.get(nasa_api_url + "rest/v1/feed?start_date=" + request_date + "&end_date=" + request_date + "&api_key=" + nasa_api_key)

	# Printing NASA request response data
	logger.info("Response status code: " + str(r.status_code))
	logger.info("Response headers: " + str(r.headers))
	logger.info("Response content: " + str(r.text))
	# Response status code is 200
	if r.status_code == 200:
		# Converting json data to python json library
		json_data = json.loads(r.text)
		# Making lists for counting safe and hazardous asteroids
		ast_safe = []
		ast_hazardous = []
		# Total asteroid count from today
		if 'element_count' in json_data:
			ast_count = int(json_data['element_count'])
			# Prints total count of nearby asteroids
			logger.info("Asteroid count today: " + str(ast_count))
			# Check if asteroid coun is more than 0
			# Entire process prints out info about nearby asteroids, including name, link to info, diameter, if it's hazardous, how close it approaches Earth, time in UTC timezone, time in it's local timezone, speed, miss distance
			if ast_count > 0:
 				for val in json_data['near_earth_objects'][request_date]:
						if 'name' and 'nasa_jpl_url' and 'estimated_diameter' and 'is_potentially_hazardous_asteroid' and 'close_approach_data' in val:
							# Sets temporary values for asteroid's name and url
							tmp_ast_name = val['name']
							tmp_ast_nasa_jpl_url = val['nasa_jpl_url']
							# Getting id of asteroid
							tmp_ast_id = val['id']
						# Sets temporary values for asteroid's estimated diameter - minimum and maximum values
						if 'kilometers' in val['estimated_diameter']:
							if 'estimated_diameter_min' and 'estimated_diameter_max' in val['estimated_diameter']['kilometers']:
								# Sets both diameter values with 3 decimal points (0.001)
								tmp_ast_diam_min = round(val['estimated_diameter']['kilometers']['estimated_diameter_min'], 3)
								tmp_ast_diam_max = round(val['estimated_diameter']['kilometers']['estimated_diameter_max'], 3)
							else:
								tmp_ast_diam_min = -2
								tmp_ast_diam_max = -2
						else:
							tmp_ast_diam_min = -1
							tmp_ast_diam_max = -1
						# Sets temporary value for if the asteroid is hazardous 
						tmp_ast_hazardous = val['is_potentially_hazardous_asteroid']
						# Checks if length of close approach value is more than 0
						# Sets temporary values for asteroid's approach data
						if len(val['close_approach_data']) > 0:
							if 'epoch_date_close_approach' and 'relative_velocity' and 'miss_distance' in val['close_approach_data'][0]:
                                	        		# Sets temporary values for the date of appraoch
								tmp_ast_close_appr_ts = int(val['close_approach_data'][0]['epoch_date_close_approach']/1000)
								tmp_ast_close_appr_dt_utc = datetime.utcfromtimestamp(tmp_ast_close_appr_ts).strftime('%Y-%m-%d %H:%M:%S')
								tmp_ast_close_appr_dt = datetime.fromtimestamp(tmp_ast_close_appr_ts).strftime('%Y-%m-%d %H:%M:%S')
		                        	                # Sets temporary values for asteroid's speed
								if 'kilometers_per_hour' in val['close_approach_data'][0]['relative_velocity']:
									tmp_ast_speed = int(float(val['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']))
								else:
									tmp_ast_speed = -1
		                        	                # Sets temporary values for distance form Earth
								if 'kilometers' in val['close_approach_data'][0]['miss_distance']:
									tmp_ast_miss_dist = round(float(val['close_approach_data'][0]['miss_distance']['kilometers']), 3)
								else:
									tmp_ast_miss_dist = -1
							else:
								tmp_ast_close_appr_ts = -1
								tmp_ast_close_appr_dt_utc = "1969-12-31 23:59:59"
								tmp_ast_close_appr_dt = "1969-12-31 23:59:59"
						# Prints predermined values if length of close approach data was less than 0
						else:
							logger.warning("No close approach data in message")
							tmp_ast_close_appr_ts = 0
							tmp_ast_close_appr_dt_utc = "1970-01-01 00:00:00"
							tmp_ast_close_appr_dt = "1970-01-01 00:00:00"
							tmp_ast_speed = -1
							tmp_ast_miss_dist = -1
						# Prints compiled information about asteroid using previously checked and set values
						logger.info("------------------------------------------------------- >>")
						logger.info("Asteroid name: " + str(tmp_ast_name) + " | INFO: " + str(tmp_ast_nasa_jpl_url) + " | Diameter: " + str(tmp_ast_diam_min) + " - " + str(tmp_ast_diam_max) + " km | Hazardous: " + str(tmp_ast_hazardous))
						logger.info("Close approach TS: " + str(tmp_ast_close_appr_ts) + " | Date/time UTC TZ: " + str(tmp_ast_close_appr_dt_utc) + " | Local TZ: " + str(tmp_ast_close_appr_dt))
						logger.info("Speed: " + str(tmp_ast_speed) + " km/h" + " | MISS distance: " + str(tmp_ast_miss_dist) + " km")
					
						# Adding asteroid data to the corresponding array
						if tmp_ast_hazardous == True:
							ast_hazardous.append([tmp_ast_name, tmp_ast_nasa_jpl_url, tmp_ast_diam_min, tmp_ast_diam_max, tmp_ast_close_appr_ts, tmp_ast_close_appr_dt_utc, tmp_ast_close_appr_dt, tmp_ast_speed, tmp_ast_miss_dist, tmp_ast_id])
						else:
							ast_safe.append([tmp_ast_name, tmp_ast_nasa_jpl_url, tmp_ast_diam_min, tmp_ast_diam_max, tmp_ast_close_appr_ts, tmp_ast_close_appr_dt_utc, tmp_ast_close_appr_dt, tmp_ast_speed, tmp_ast_miss_dist, tmp_ast_id])
			# Prints that no asteroids will hit Earth if the total asteroid count for the day is 0
			else:
				logger.info("No asteroids are going to hit earth today")
		# Prints the number of detected hazardous and safe asteroids using the length of the list for both values
		logger.info("Hazardous asteorids: " + str(len(ast_hazardous)) + " | Safe asteroids: " + str(len(ast_safe)))
		# Checks if there are any hazardous asteroids at all
		if len(ast_hazardous) > 0:
			# Sorts hazardous asteroid list by how hazardous, from smallest to biggest value
			ast_hazardous.sort(key = lambda x: x[4], reverse=False)
			# Prints posible asteroid impacts today, as well as a link to its url
			logger.info("Today's possible apocalypse (asteroid impact on earth) times:")
			for asteroid in ast_hazardous:
				logger.info(str(asteroid[6]) + " " + str(asteroid[0]) + " " + " | more info: " + str(asteroid[1]))

			ast_hazardous.sort(key = lambda x: x[8], reverse=False)
			# Prints closest hazardous asteroid to Earth with its information
			logger.info("Closest passing distance is for: " + str(ast_hazardous[0][0]) + " at: " + str(int(ast_hazardous[0][8])) + " km | more info: " + str(ast_hazardous[0][1]))
			push_asteroids_arrays_to_db(request_date, ast_hazardous, 1)
		# If no hazardous asteroids were spotted today, prints that
		else:
			logger.info("No asteroids close passing earth today")
		if len(ast_safe) > 0:
			push_asteroids_arrays_to_db(request_date, ast_safe, 0)
	else:
		logger.debug("Unable to get response from API. Response code: " + str(r.status_code) + " | content: " + str(r.text))
