from flask import Flask
from flask_mqtt import Mqtt

airtemp = "airtemp: Not Available"

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'localhost'  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

mqtt = Mqtt(app)

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
	print("MQTT connected")
	mqtt.subscribe('airtemp')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
	print("MQTT received: " + message.topic + "=" + message.payload.decode())
	if message.topic == "airtemp":
		global airtemp
		airtemp = "airtemp: " + message.payload.decode()

@app.route('/')
def index():
    return airtemp

if __name__ == '__main__':
	app.run(debug=True, port=80, host='0.0.0.0')
