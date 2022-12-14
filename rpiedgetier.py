import signal, sys, time, glob
import serial
import string
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import datetime

# Building indentifier -> a raspberry pi corresponds to a building
thisBuilding = "building0"

# defines MQTT broker IP address
mqttAddress = "52.63.215.247"

# creates a map between bluetooth devices and their aliases.
# The devices ID can be queried with the WHOAREYOU command
macMap = {"4cebd67640400":"door01","cb815f2e96800":"door02"}

# Control flag that switches when emergency state change is
# requested or serviced
emergencyTrigger = False

# Current emergency state for this building
emergencyState = "OFF"

# This will perform a Bluetooth network discovery
serialMap = dict()
ports = glob.glob('/dev/rfcomm*')
for port in ports:
	try:
		s = serial.Serial(port)
		s.write(str.encode("WHOAREYOU\r\n"))
		rawResponse = s.readline()
		response = rawResponse.decode('utf-8').strip('\r\n').split(',')
		assetName = macMap[response[1]]
		serialMap[assetName] = s
		print("Asset " + assetName + " added to serialMap")
	except (OSError, serial.SerialException):
		pass

# structure that temporarily holds credentials in case the cloud
# tier goes down
CredentialBuffer = dict()

# maximum time credentials are allowed to be buffered before
# becoming stale in seconds
BUFFERING_TIME_MAX = 60

# to keep cloud connection status
CloudConnected = False

def on_connect(client, userdata, flags, rc): # func for making connection
	global CloudConnected
	CloudConnected = True
	print("Connecting to MQTT")
	print("Connection returned result: " + str(rc))
	# subscribe to any emergency commands to this building
	client.subscribe(thisBuilding + "/emergency")
	# subscribe to any access responses to any tags in this building
	client.subscribe(thisBuilding + "/+/access/#")

def on_message(client, userdata, msg): # func for sending msg
	payload = msg.payload.decode("utf-8")
	topicLevels = msg.topic.split('/')
	numLevels = len(topicLevels)
	print("numLevels ", numLevels)
	print("### received from MQTT broker: " + msg.topic + " " + payload)
	payload = msg.payload.decode().strip()

	if numLevels > 1:
		building = topicLevels[0]
		level2 = topicLevels[1]
		if level2 == "emergency":
			global emergencyState, emergencyTrigger
			emergencyState = "ON" if payload == "1" else "OFF"
			emergencyTrigger = True
		elif numLevels == 4:
			level3 = topicLevels[2]
			if level3 == "access":
				tagID = topicLevels[3]
				permission = "DENIED"
				if payload == "1":
					permission = "GRANTED"
					bufferCredential(tagID, level2)
				try:
					serialMap[level2].write(str.encode("ACCESS," + permission + "\r\n"))
					print(str.encode("ACCESS," + permission + "\r\n"))
				except:
					print("Asset not found: " + level2)
					print(serialMap)

def on_publish(client, obj, msg):
	print("Published to MQTT message id: " + str(msg))

def on_disconnect(client, userdata, rc):
	if rc != 0:
		global CloudConnected
		CloudConnected = False
		print("MQTT disconnected. Attempting to reconnect.")

def bufferCredential(tagID, assetID):
	global CredentialBuffer
	GrantTime = datetime.datetime.now()
	CredentialBuffer[tagID + "," + assetID] = GrantTime

def bufferedResponse(tagID, asset):
	key = tagID + "," + asset
	access = "DENIED"
	if key in CredentialBuffer:
		# Check elapsed time since last access granted online
		now = datetime.datetime.now()
		elapsedTime = now - CredentialBuffer[key]
		if elapsedTime.total_seconds() < BUFFERING_TIME_MAX :
			access = "GRANTED"
	else:
		print("Credential not found: " + tagID + "," + asset)

	if asset in serialMap:
		serialMap[asset].write(str.encode("ACCESS," + access + "\r\n"))
	else:
		print("Could not find asset: " + asset)

def processAllSerials():
	for asset in serialMap:
		serial = serialMap[asset]

		global emergencyTrigger
		if emergencyTrigger:
			print("emergency state: ", emergencyState)
			serial.write(str.encode("EMERGENCY," + emergencyState + "\r\n"))

		if serial.in_waiting > 0:
			rawserial = serial.readline()
			cookedserial = rawserial.decode('utf-8').strip('\r\n')
			print("Received via bt: " + cookedserial + "\n")

			# it is good practice to avoid jamming the data
			# bandwidth used in wireless communications of IoT
			# devices. So I used comma separated values to
			# encode sensed data collected from sensors. Now
			# I'll split them back.
			values = cookedserial.split(",")

			# the message may come broken down and we need to
			# avoid accessing an element out-of-bounds of the
			# array.
			valuesLen = len(values)

			if valuesLen == 2:
				if values[0] == "TAGSWIPE":
					TagID = values[1]
					if CloudConnected :
						client.publish(thisBuilding +"/" + asset + "/tagswipe", TagID, qos=2)
						print("published: " +thisBuilding +"/" + asset + "/tagswipe/" + TagID)
					else:
						bufferedResponse(TagID, asset)

	# Clears the emergency trigger once all serials
	# are sent the emergency message
	emergencyTrigger = False


def signal_handler(sig, frame):
	print('Exiting???')
	sys.exit()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_disconnect = on_disconnect
client.username_pw_set(username="", password="")
client.connect(mqttAddress, 1883, 2)

# So we can handle user input
signal.signal(signal.SIGINT, signal_handler)

# Variable to store last time we attempted reconnection
SinceReconnect = datetime.datetime.now()

mqttConnInitiated = False

while True:
	try:
		client.loop()
		if not CloudConnected:
			now = datetime.datetime.now()
			elapsed = now - SinceReconnect
			if elapsed.seconds > 10:
				SinceReconnect = now
				client.reconnect()
				print("Attempting to reconnect???")
		processAllSerials()
	except Exception as e:
		print("An error has occured: ", e)
