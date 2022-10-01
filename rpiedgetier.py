import signal, sys, time
import serial
import string
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import datetime

# Building indentifier -> a raspberry pi corresponds to a building
thisBuilding = "building0"

# defines MQTT broker IP address
mqttAddress = "52.63.215.247"

# reading and writing data from and to BT serial
# rfcomm0 corresponds to the bluetooth device representing door01
ser = serial.Serial("/dev/rfcomm0", 9600)
serialMap = {"door01":ser}

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
			emergencyState = "ON" if payload == "1" else "OFF"
			print("emergency state: ", emergencyState)
			ser.write(str.encode("EMERGENCY," + emergencyState + "\r\n"))
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


def signal_handler(sig, frame):
	print('Exiting…')
	sys.exit()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_disconnect = on_disconnect
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
				print("Attempting to reconnect…")
		processAllSerials()
	except Exception as e:
		print("An error has occured: ", e)
