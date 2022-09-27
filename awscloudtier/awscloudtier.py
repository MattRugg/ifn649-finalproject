import datetime
from flask import Flask, render_template, request, session
from flask_mqtt import Mqtt
import urllib
from markupsafe import Markup

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'localhost'  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

mqtt = Mqtt(app)

permTable = dict()
permTable['building0/door01/07003048EC93'] = ['building0','door01','07003048EC93',1]
permTable['building0/door02/07003048EC93'] = ['building0','door02','07003048EC93',0]

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
				permItem = permTable[idx]
				if permItem[3] == 1:
					access = '1'
			except:
				print("Not record found in the permissions Table: ", idx)
			mqtt.publish(building + '/' + asset +'/access/' + tagID, access)
			global accessLog
			time = datetime.datetime.now()
			accessLog.append([building, asset, tagID, access, time])



@app.template_filter('urlencode')
def urlencode_filter(s):
	if type(s) == 'Markup':
		s = s.unescape()
	s = s.encode('utf8')
	s = urllib.parse.quote_plus(s)
	return Markup(s)

@app.route('/logout')
def webLogout():
	session['loggedin'] = False
	return webLogin()

@app.route('/login')
def webLogin():
	return render_template('login.html')

@app.route('/removepermission', methods=['GET', 'POST'])
def webRemovePermission():
	if not session['loggedin']:
		return webLogin()

	permissionItemId = request.args.get('id', '')
	permissionItemId = urllib.parse.unquote(permissionItemId)
	if permissionItemId in permTable:
		permTable.pop(permissionItemId)
		return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Permission removed")

	return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Nothing to remove")

@app.route('/addpermission', methods = ['POST','GET'])
def webAddPermission():
	if not session['loggedin']:
		return webLogin()

	if request.method == 'POST':
		building = request.form.get('building', 'invalid building')
		asset = request.form.get('asset', 'invalid asset')
		tagid = request.form.get('tagId', 'invalid tag')
		permission = request.form.get('grantAccess', 'off')
		permission = 1 if permission == 'on' else 0
		permTable[building + '/' + asset + '/' + tagid] = [building, asset, tagid, permission]
		print('POST request: ', request.form)
		return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Permission entry added")

	return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Nothing to add")

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
		user = request.form.get('user', '')
		pswd = request.form.get('pwd', '')
		print('POST request: ', request.form)
		if user == 'admin' and pswd == 'exxscuseme77!!a':
			session['loggedin'] = True;

	if not session['loggedin']:
		return webLogin()

	return render_template('index.html',permissionTable=permTable,accessLog=accessLog)

if __name__ == '__main__':
	app.secret_key = 'supersecretkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(debug=True, port=80, host='0.0.0.0')
