import requests
import json
import datetime
import time
import yaml

from datetime import datetime
from configparser import ConfigParser
print('Asteroid processing service')

# Initiating and reading config values
print('Loading configuration from file')

try:
	config = ConfigParser()
	config.read('config.ini')

	nasa_api_key = config.get('nasa', 'api_key')
	nasa_api_url = config.get('nasa', 'api_url')
except:
	logger.exception('')
print('DONE')

# Getting todays date
dt = datetime.now()
request_date = str(dt.year) + "-" + str(dt.month).zfill(2) + "-" + str(dt.day).zfill(2)  
print("Generated today's date: " + str(request_date))

# Requesting INFO from NASA API
print("Request url: " + str(nasa_api_url + "rest/v1/feed?start_date=" + request_date + "&end_date=" + request_date + "&api_key=" + nasa_api_key))
r = requests.get(nasa_api_url + "rest/v1/feed?start_date=" + request_date + "&end_date=" + request_date + "&api_key=" + nasa_api_key)

# Printing NASA request response data
print("Response status code: " + str(r.status_code))
print("Response headers: " + str(r.headers))
print("Response content: " + str(r.text))
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
		print("Asteroid count today: " + str(ast_count))
		# Check if asteroid coun is more than 0
		# Entire process prints out info about nearby asteroids, including name, link to info, diameter, if it's hazardous, how close it approaches Earth, time in UTC timezone, time in it's local timezone, speed, miss distance
		if ast_count > 0:
 			for val in json_data['near_earth_objects'][request_date]:
					if 'name' and 'nasa_jpl_url' and 'estimated_diameter' and 'is_potentially_hazardous_asteroid' and 'close_approach_data' in val:
					# Sets temporary values for asteroid's name and url
						tmp_ast_name = val['name']
						tmp_ast_nasa_jpl_url = val['nasa_jpl_url']
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
						print("No close approach data in message")
						tmp_ast_close_appr_ts = 0
						tmp_ast_close_appr_dt_utc = "1970-01-01 00:00:00"
						tmp_ast_close_appr_dt = "1970-01-01 00:00:00"
						tmp_ast_speed = -1
						tmp_ast_miss_dist = -1
					# Prints compiled information about asteroid using previously checked and set values
					print("------------------------------------------------------- >>")
					print("Asteroid name: " + str(tmp_ast_name) + " | INFO: " + str(tmp_ast_nasa_jpl_url) + " | Diameter: " + str(tmp_ast_diam_min) + " - " + str(tmp_ast_diam_max) + " km | Hazardous: " + str(tmp_ast_hazardous))
					print("Close approach TS: " + str(tmp_ast_close_appr_ts) + " | Date/time UTC TZ: " + str(tmp_ast_close_appr_dt_utc) + " | Local TZ: " + str(tmp_ast_close_appr_dt))
					print("Speed: " + str(tmp_ast_speed) + " km/h" + " | MISS distance: " + str(tmp_ast_miss_dist) + " km")
					
					# Adding asteroid data to the corresponding array
					if tmp_ast_hazardous == True:
						ast_hazardous.append([tmp_ast_name, tmp_ast_nasa_jpl_url, tmp_ast_diam_min, tmp_ast_diam_max, tmp_ast_close_appr_ts, tmp_ast_close_appr_dt_utc, tmp_ast_close_appr_dt, tmp_ast_speed, tmp_ast_miss_dist])
					else:
						ast_safe.append([tmp_ast_name, tmp_ast_nasa_jpl_url, tmp_ast_diam_min, tmp_ast_diam_max, tmp_ast_close_appr_ts, tmp_ast_close_appr_dt_utc, tmp_ast_close_appr_dt, tmp_ast_speed, tmp_ast_miss_dist])
		# Prints that no asteroids will hit Earth if the total asteroid count for the day is 0
		else:
			print("No asteroids are going to hit earth today")
	# Prints the number of detected hazardous and safe asteroids using the length of the list for both values
	print("Hazardous asteorids: " + str(len(ast_hazardous)) + " | Safe asteroids: " + str(len(ast_safe)))
	# Checks if there are any hazardous asteroids at all
	if len(ast_hazardous) > 0:
		# Sorts hazardous asteroid list by how hazardous, from smallest to biggest value
		ast_hazardous.sort(key = lambda x: x[4], reverse=False)
		# Prints posible asteroid impacts today, as well as a link to its url
		print("Today's possible apocalypse (asteroid impact on earth) times:")
		for asteroid in ast_hazardous:
			print(str(asteroid[6]) + " " + str(asteroid[0]) + " " + " | more info: " + str(asteroid[1]))

		ast_hazardous.sort(key = lambda x: x[8], reverse=False)
		# Prints closest hazardous asteroid to Earth with its information
		print("Closest passing distance is for: " + str(ast_hazardous[0][0]) + " at: " + str(int(ast_hazardous[0][8])) + " km | more info: " + str(ast_hazardous[0][1]))
	# If no hazardous asteroids were spotted today, prints that
	else:
		print("No asteroids close passing earth today")

else:
	print("Unable to get response from API. Response code: " + str(r.status_code) + " | content: " + str(r.text))
