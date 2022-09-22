import serial
import time
import string
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

thisBuilding = "Building0"

# defines which tty device we should use to communicate
# via bluetooth
ttyBluetooth = "/dev/rfcomm0"

# defines MQTT broker IP address
mqttAddress = "54.193.132.176"

# reading and writing data from and to teensy via serial
# rfcomm0 corresponds to the bluetooth device
ser = serial.Serial(ttyBluetooth, 9600)

def on_connect(client, userdata, flags, rc): # func for making connection
	print("Connecting to MQTT")
	print("Connection returned result: " + str(rc))
	client.subscribe(thisBuilding + "/emergency")
	client.subscribe(thisBuilding + "/+/access")

def on_message(client, userdata, msg): # func for sending msg
	payload = msg.payload.decode("utf-8")
	topicLevels = msg.topic.split('/')
	numLevels = len(topicLevels)
	if nulLevels > 2:
		building = topicLevels[0]
		if (building == thisBuilding):
			level2 = topicLevels[1]
			level3 = topicLevels[2]
			if level2 == "emergency":
				emergencyState = "OFF" if level == "0" else "ON"
				ser.write(str.encode("EMERGENCY," + emergencyState + "\r\n"))
			elif level2[:4] == "door" and numLevels > 4:
				doorNumber = level2[4:]
				if level3 == "access":
					tagID = topicLevels[3]
					permission = "DENIED"
					if topicLevels[4] == 1:
						permission = "GRANTED"
						bufferCredential(tagID, level2)
					if doorNumber == 1:
						ser.write(str.encode("ACCESS," + emergencyState + "\r\n"))
	print("### received from MQTT broker: " + msg.topic + " " + payload)

def on_publish(client, obj, msg):
	print("Published to MQTT message id: " + str(msg))

def bufferCredential(tagID, assetID):
	#TODO buffer credential
	pass


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.connect(mqttAddress, 1883, 60)

while True:
	client.loop()

	if ser.in_waiting > 0:
		rawserial = ser.readline()

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
				client.publish(thisBuilding +"/door1/tagswipe", TagID)
