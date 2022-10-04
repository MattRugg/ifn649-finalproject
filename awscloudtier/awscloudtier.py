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
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''

mqtt = Mqtt(app)

# Structure will hold access history
accessLog = []
# Set to True whenever an access entry has been added
# or permission has changed so the page can be updated
infoUpdated = False
# All buildings listed in the permissions file
buildingTable = []

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

	with open('permtable.txt', 'r') as permFile:
		Lines = permFile.readlines()
	for line in Lines:
		# split comma separated lines
		nline = line.strip('\n')
		lineItems = nline.split(",")
		if hashS == lineItems[0]:
			return [lineItems[1], lineItems[2], lineItems[3], lineItems[4]]
	return None

# Checks if building already exists in the building file
def hasBuilding(building):
	Lines = []

	with open('buildings.txt', 'r') as buildingFile:
		Lines = buildingFile.readlines()
	for line in Lines:
		if building == line.strip('\n'):
			return True
	return False

# Adds a new building to the building table file
def addBuilding(building):
	# add building if it does not exist
	if not hasBuilding(building):
		with open('buildings.txt', mode='a+') as permFile:
			permFile.write(building + ',0\n')
		return True
	return False

# Adds a new permission entry to the permissions table file
def addPermEntry(building, asset, tagId, permission):
	entryHash = Hash(building + '/' + asset + '/' + tagId)
	# check if entry already exists
	entryExisting = getPermEntry(entryHash)
	# add if it does not exist
	if entryExisting is None:
		with open('permtable.txt', mode='a+') as permFile:
			permFile.write(str(entryHash) + ',' + building + ',' + asset + ',' + tagId + ',' + permission + '\n')
		addBuilding(building)
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
	for line in Lines:
		# split comma separated lines
		nline = line.strip('\n')
		lineItems = nline.split(",")
		permTable[lineItems[0]] = [lineItems[1], lineItems[2], lineItems[3], lineItems[4]]
	return permTable

# Reads permission entry from permission table file
def getBuildingTable():
	Lines = []
	buildingTable = []
	# Read all lines onto buildingTable
	with open('buildings.txt', 'r') as buildingFile:
		Lines = buildingFile.readlines()
	for line in Lines:
		# split comma separated lines
		nline = line.strip('\n')
		lineItems = nline.split(",")
		buildingTable.append([lineItems[0],lineItems[1]])
	return buildingTable

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
			global accessLog, infoUpdated
			time = datetime.datetime.now()
			accessLog.append([building, asset, tagID, access, time])
			infoUpdated = True
			print("access updated")

@app.template_filter('urlencode')
def urlencode_filter(s):
	if type(s) == 'Markup':
		s = s.unescape()
	s = s.encode('utf8')
	s = urllib.parse.quote_plus(s)
	return Markup(s)

@app.route('/update')
def webUpdate(message=''):
	global infoUpdated

	# default answer: no updates were made
	jsonResponse = '{"update":false}'

	if not session['loggedin']:
		return jsonResponse

	if infoUpdated:
		jsonResponse = '{"update":true,"message":"'
		jsonResponse += message+'"}'
		infoUpdated = False

	return jsonResponse

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
		return webUpdate()

	permissionItemId = request.args.get('id', '')
	permissionItemId = int(urllib.parse.unquote(permissionItemId))
	permItem = getPermEntry(permissionItemId)
	if permissionItemId is None:
		retMessage = "Could not remove permission because it does not exist"
	else:
		retMessage = "Permission record removed"
		global infoUpdated
		removePermEntry(permissionItemId)
		infoUpdated = True

	return webUpdate(retMessage)

@app.route('/togglepermission', methods=['GET', 'POST'])
def webTogglePermission():
	if not session['loggedin']:
		return webUpdate()

	permissionItemId = request.args.get('id', '')
	permissionItemId = int(urllib.parse.unquote(permissionItemId))
	permItem = getPermEntry(permissionItemId)
	if permissionItemId is None:
		retMessage = "Could not toggle permission because it does not exist"
	else:
		retMessage = "Permission record changed"
		global infoUpdated
		togglePermEntry(permissionItemId)
		infoUpdated = True

	return webUpdate(retMessage)

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
		permTable = getPermTable()
		return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Permission entry added")

	permTable = getPermTable()
	return render_template('index.html',permissionTable=permTable,accessLog=accessLog, message="Nothing to add")

@app.route('/emergency')
def webEmergency():
	jsonResponse = '{"triggered":false,"message":"You are not logged in"}';

	if not session['loggedin']:
		return jsonResponse

	emergencyReq = request.args.get('state', 'false')
	emergencyStateReq = True if emergencyReq == 'true' else False;
	print('state ',emergencyStateReq)
	building = request.args.get('building', 'no building')
	global accessLog, infoUpdated
	time = datetime.datetime.now()
	infoUpdated = True

	if (emergencyStateReq):
		jsonResponse = '{"triggered":true,"message":"Emergency triggered for '
		jsonResponse += building +'"}';
		mqtt.publish(building + '/emergency','1')
		accessLog.append([building, "Emergency", "", "3", time])
	else:
		jsonResponse = '{"triggered":false,"message":"Emergency terminate for'
		jsonResponse += building +'"}';
		mqtt.publish(building + '/emergency','0')
		accessLog.append([building, "Emergency", "", "4", time])

	# We also need to updated the building emergency state in the file
	with open("buildings.txt", "r") as f:
		lines = f.readlines()
	with open("buildings.txt", "w") as f:
		for line in lines:
			nline = line.strip('\n')
			items = nline.split(',')
			newState = '1' if emergencyStateReq else '0'
			if items[0] == building:
				f.write(items[0] + ',' + newState + '\n')
			else:
				f.write(line)

	return jsonResponse

@app.route('/', methods = ['POST','GET'])
def webIndex():
	# We need to make sure the web user has been
	# authenticated before using the system.
	if 'loggedin' not in session:
		session['loggedin'] = False;

	if request.method == 'POST':
		user = request.form.get('user', '')
		pswd = request.form.get('pwd', '')
		if user == 'admin' and pswd == 'exxscuseme77!!a':
			session['loggedin'] = True;
		message = request.form.get('message', '')

	if not session['loggedin']:
		return webLogin()

	permTable = getPermTable()
	buildingTable = getBuildingTable()
	if 'message' in locals():
		return render_template('index.html',permissionTable=permTable,buildingTable=buildingTable,accessLog=accessLog,message=message)
	else:
		return render_template('index.html',permissionTable=permTable,buildingTable=buildingTable,accessLog=accessLog)

# Add default entries if necesary
addPermEntry('building0','door01','07003048EC93','1')
addPermEntry('building0','door02','07003048EC93','0')
addPermEntry('building0','door01','0B0042739CA6','0')
addPermEntry('building0','door02','0B0042739CA6','1')

if __name__ == '__main__':
	app.secret_key = 'supersecretkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(debug=True, port=80, host='0.0.0.0')
