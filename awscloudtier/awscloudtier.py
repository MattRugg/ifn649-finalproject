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

# Structure will hold access history
accessLog = []

# Creates our own hash as the native Python function
# has a random seed which will mess the permissions
# table usage
def Hash(text:str):
	hash=0
	for ch in text:
		hash = ( hash*281  ^ ord(ch)*997) & 0xFFFFFFFF
	return hash

# Reads permission entry from permission table file
def getPermEntry(hash):
	hashS = str(hash)
	Lines = []
	# Using readlines()
	with open('permtable.txt', 'r') as permFile:
		Lines = permFile.readlines()
	for line in Lines:
		# split comma separated lines
		nline = line.strip('\n')
		lineItems = nline.split(",")
		if hashS == lineItems[0]:
			return [lineItems[1], lineItems[2], lineItems[3], lineItems[4]]
	return None

# Adds a new permission entry to the permissions table file
def addPermEntry(building, asset, tagId, permission):
	entryHash = Hash(building + '/' + asset + '/' + tagId)
	# check if entry already exists
	entryExisting = getPermEntry(entryHash)
	# add if it does not exist
	if entryExisting is None:
		with open('permtable.txt', mode='a+') as permFile:
			permFile.write(str(entryHash) + ',' + building + ',' + asset + ',' + tagId + ',' + permission + '\n')
		return True
	# TODO update it if already exists
	return False

# Remove an entry from the permissions table file
def removePermEntry(hash):
	with open("permtable.txt", "r") as f:
		lines = f.readlines()
	with open("permtable.txt", "w") as f:
		for line in lines:
			items = line.split(',')
			thisHash = items[0]
			if thisHash != str(hash):
				f.write(line)

# Remove an entry from the permissions table file
def togglePermEntry(hash):
	with open("permtable.txt", "r") as f:
		lines = f.readlines()
	with open("permtable.txt", "w") as f:
		for line in lines:
			nline = line.strip('\n')
			items = nline.split(',')
			newHash = Hash(items[1] + '/' + items[2] + '/' + items[3])
			newPerm = '0' if items[4] == '1' else '1'
			if items[0] == str(hash):
				f.write(str(newHash) + ',' + items[1] + ',' + items[2] + ',' + items[3] + ',' + newPerm + '\n')
			else:
				f.write(line)

# Reads permission entry from permission table file
def getPermTable():
	Lines = []
	permTable = dict()
	# Read all lines onto permTable
	with open('permtable.txt', 'r') as permFile:
		Lines = permFile.readlines()
	count = 0
	for line in Lines:
		# split comma separated lines
		nline = line.strip('\n')
		lineItems = nline.split(",")
		permTable[lineItems[0]] = [lineItems[1], lineItems[2], lineItems[3], lineItems[4]]
	return permTable

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
				hash = Hash(building + '/' + asset + '/' + tagID)
				permItem = getPermEntry(hash)
				if permItem is not None:
					if permItem[3] == '1':
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
	permissionItemId = int(urllib.parse.unquote(permissionItemId))
	permItem = getPermEntry(permissionItemId)
	if permissionItemId is not None:
		removePermEntry(permissionItemId)
		permTable = getPermTable()
		return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Permission removed")

	permTable = getPermTable()
	return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Nothing to remove")

@app.route('/togglepermission', methods=['GET', 'POST'])
def webTogglePermission():
	if not session['loggedin']:
		return webLogin()

	permissionItemId = request.args.get('id', '')
	permissionItemId = int(urllib.parse.unquote(permissionItemId))
	permItem = getPermEntry(permissionItemId)
	if permissionItemId is not None:
		togglePermEntry(permissionItemId)
		permTable = getPermTable()
		return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Permission changed")

	permTable = getPermTable()
	return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Nothing to change")

@app.route('/addpermission', methods = ['POST','GET'])
def webAddPermission():
	if not session['loggedin']:
		return webLogin()

	if request.method == 'POST':
		building = request.form.get('building', 'invalid building')
		asset = request.form.get('asset', 'invalid asset')
		tagid = request.form.get('tagId', 'invalid tag')
		permission = request.form.get('grantAccess', 'off')
		permission = '1' if permission == 'on' else '0'
		addPermEntry(building, asset, tagid, permission)
		print('POST request: ', request.form)
		permTable = getPermTable()
		return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Permission entry added")

	permTable = getPermTable()
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

	permTable = getPermTable()
	return render_template('index.html',permissionTable=permTable,accessLog=accessLog)

# Add default entries if necesary
addPermEntry('building0','door01','07003048EC93','1')
addPermEntry('building0','door02','07003048EC93','0')
addPermEntry('building0','door01','0B0042739CA6','0')
addPermEntry('building0','door02','0B0042739CA6','1')

if __name__ == '__main__':
	app.secret_key = 'supersecretkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(debug=True, port=80, host='0.0.0.0')
