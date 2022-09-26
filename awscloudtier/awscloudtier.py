from flask import Flask, render_template, request, session
from flask_mqtt import Mqtt

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'localhost'  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

mqtt = Mqtt(app)

permTable = dict()
permTable['building0/door01/07003048EC93'] = 1
#permTable['building0/door01/07003048EC93'] = 1
#permTable['building0/door01/07003048EC93'] = 1
#permTable['building0/door01/07003048EC93'] = 1
#permTable['building0/door01/07003048EC93'] = 1

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
	print("MQTT connected")
	mqtt.subscribe('#')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, msg):
	print("MQTT received: " + msg.topic + "=" + msg.payload.decode())
	topicLevels = msg.topic.split('/')
	numLevels = len(topicLevels)

	if numLevels == 3:
		building = topicLevels[0]
		asset = topicLevels[1]
		tagswipe = topicLevels[2]
		tagID = msg.payload.decode()
		if tagswipe == "tagswipe":
			access = '0'
			try:
				idx = building + '/' + asset + '/' + tagID
				if permTable[idx] == 1:
					access = '1'
			except:
				print("Not record found in the permissions Table: ", idx)
			mqtt.publish(building + '/' + asset +'/access/' + tagID, access)



@app.route('/logout')
def webLogout():
	session['loggedin'] = False
	return webLogin()

@app.route('/login')
def webLogin():
	return render_template('login.html')

@app.route('/emergency')
def webEmergency():
	mqtt.publish('led','on')
	return index()

@app.route('/', methods = ['POST','GET'])
def index():
	# We need to make sure the web user has been
	# authenticated before using the system.
	if 'loggedin' not in session:
		session['loggedin'] = False;

	if request.method == 'POST':
		user = request.form.get('user', False)
		pswd = request.form.get('pwd', False)
		print('POST request: ', request.form)
		if user == 'admin' and pswd == '1234':
			session['loggedin'] = True;

	if not session['loggedin']:
		return webLogin()

	return render_template('index.html')

	# HTML header tags
	retHTML  = "<html><head><title>IFN649 Assessment </title>"

	# basic styling
	retHTML += "<style>body{font-family:verdana;font-size:14px;background-color: #eee;}"
	retHTML += "a{padding:15px;text-align:center;color:black;margin:5px;border-radius:10px;display:inline-block;text-decoration:none;background-image:linear-gradient(to bottom right, cyan, #c6f6c6);}"
	retHTML += "div{margin:auto;width:400px;border-radius:10px;background-color:white;padding:10px 30px 20px}</style></head>"

	# Title block
	retHTML += "<body><div style='margin-top:40px;margin-bottom:10px;background-image:linear-gradient(to bottom right, cyan, #c6f6c6)'><h2>IFN649 Assessment 1</h2></h3>Matheus Cavalca Ruggiero<br />N10913556</h3></div>"

	# update fields according to MQTT messages
	retHTML += "<div><p>logged in</p>"

	# operate actuators
	retHTML += "<a href='/logout'>Logout</a>"

	retHTML += "</div></body></html>"
	return retHTML

if __name__ == '__main__':
	app.secret_key = 'supersecretkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(debug=True, port=80, host='0.0.0.0')
