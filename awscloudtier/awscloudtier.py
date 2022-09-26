import datetime
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
permTable['building0/door02/07003048EC93'] = 0
#permTable['building0/door01/07003048EC93'] = 1
#permTable['building0/door01/07003048EC93'] = 1
#permTable['building0/door01/07003048EC93'] = 1

accessLog = []

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
			global accessLog
			time = datetime.datetime.now()
			accessLog.append([building, asset, tagID, time])



@app.route('/logout')
def webLogout():
	session['loggedin'] = False
	return webLogin()

@app.route('/login')
def webLogin():
	return render_template('login.html')

@app.route('/addpermission')
def webAddPermission():
	if not session['loggedin']:
		return webLogin()

	if request.method == 'POST':
		building = request.form.get('building', False)
		asset = request.form.get('asset', False)
		tagid = request.form.get('tagid', False)
		permisison = request.form.get('permission', False)
		permTable[building + '/' + asset + '/' + tagid] = permission

	return render_template('index.html')

@app.route('/emergency')
def webEmergency():
	if not session['loggedin']:
		return webLogin()

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
		if user == 'admin' and pswd == 'exxscuseme77!!a':
			session['loggedin'] = True;

	if not session['loggedin']:
		return webLogin()

	return render_template('index.html')

if __name__ == '__main__':
	app.secret_key = 'supersecretkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(debug=True, port=80, host='0.0.0.0')
