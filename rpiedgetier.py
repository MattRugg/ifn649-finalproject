import serial
import time
import string
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

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
	client.subscribe("led")
	client.subscribe("buzzer")

def on_message(client, userdata, msg): # func for sending msg
	payload = msg.payload.decode("utf-8")
	if msg.topic == "buzzer":
		ser.write(str.encode("BUZZER_TRACK" + payload))
	elif msg.topic == "led":
		ser.write(str.encode("LED_" + payload))
	print("### received from MQTT broker: " + msg.topic + " " + payload)

def on_publish(client, obj, msg):
	# We won't do anything at this point with this
	# information.
	#print("### published to MQTT: " + str(msg))
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

		print("### received via bt: ")
		cookedserial = rawserial.decode('utf-8').strip('\r\n')

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

		if (valuesLen > 0):
			# we currently do not use the message id
			print("msgID: " + values[0])

		if (valuesLen > 1):
			# publish air humidity to MQTT
			print("airHumidity: " + values[1])
			client.publish("airhum", values[1])

		if (valuesLen > 2):
			# publish air temperature to MQTT
			print("airTemperature: " + values[2])
			client.publish("airtemp", values[2])

		if (valuesLen > 3):
			#publish air heat index in Celsius to MQTT
			print("airHeatIndexCelsius: " + values[3])
			client.publish("heatindex", values[3])

		if (valuesLen > 4):
			#publish soil humidity percentage to MQTT
			print("soilHumidityPercentage: " + values[4])
			client.publish("soilhum", values[4])
