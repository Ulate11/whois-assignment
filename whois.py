import bz2, json, pickle, yaml
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from whoisapi import *

# file to store the info provided by whoisxmlapi.
SAVED_DATA_FILE = '/app/yesterday.pic'
# list of domains to verify.
DOMAINS_LIST_FILE = '/app/domains.yml'

# the following is sensitive data, please clean values when publishing the code on public sities like github.

#api key for whoisxmlapi
apiKey = 'your whoisxmlapi key'

# email credentials for sending emails.
smtpPort = 587
smtpServer = 'smtp.gmail.com'
senderMail = 'your email'
senderPw = 'your password'
recipients = ["<mail1>", "<mail2>"]

client = None

# old data loaded from file
yesterdayData = {}
# current data provided by whoisxmlapi
currentData = {}
# domains with updated information, these will be send by e-mail.
updatedData = {}

def loadSettings():
	global senderMail, senderPw, smtpServer, smtpPort, recipients, apiKey
	y = loadYaml("/app/appSettings.yaml")
	senderMail = y['senderMail']
	senderPw = y['senderPassword']
	recipients = y['recipients']
	smtpServer = y['smtpServer']
	smtpPort = y['smtpPort']
	apiKey = y['whoisApiKey']

def setWhoisClient():
	global client
	client = Client(api_key = apiKey)

def loadPickle(path:str):
	""" loads a compressed pickle file
	@param path: the string path to the file to be loaded
	@return: the pyhton object from the file.
	"""
	b = bz2.BZ2File(path, 'rb')
	return pickle.load(b)

def savePickle(d, path:str):
	""" saves the provided data in the specified path, pickled and compressed in bz2 format.
	@param d: the python object to be saved.
	@param path: the file to the file in the disk. This file will be replaced if exist.
	"""
	f= bz2.BZ2File(path, 'wb')
	pickle.dump(d, f, 4)
	f.close()

def getDomainInfo(domain:str):
	""" ask to whoisxmlapi for the information of the domain specified.
	note: set the client variable before using this function.
	@param domain: a str with the domain
	@return whois object.
	"""
	return client.data(domain)

def loadYaml(path:str):
	""" loads a yaml file from the specified path.
	@param path: path to te yaml file.
	@return the loaded yaml in memory.
	"""
	with open(path) as f:
		return yaml.full_load(f)

def setEmail(d, customField, w):
	""" this function checks if the field 'email' exist in the specified object, and checks if the field is not blank. If previous conditions are true, add the value to the provided dictionary in the specified customField.
	@param d: the dictionary to add the field, if this field exist.
	@param customField: the name of the field as the value will be added to the dictionary.
	@param w: the object to be verified.
	"""
	try:
		email = w.email
		if email: d[customField] = email
	except:
		pass

def processDomain (domain:str):
	""" this function obtains the domain information, then takes the needed values used in this script.
	@param domain: the string domain used to obtain the info from whoisxmlapi
	@return: dictionary with the needed information for the assignment.
	"""
	print ("processing: ", domain)
	w = getDomainInfo(domain)
	data = {
		'whoisCreatedDate': w.created_date,
		'whoisUpdatedDate': w.updated_date,
		'whoisExpiresDate': w.expires_date,
		'domainName': w.domain_name
	}

	# sometimes registrant is not present. 
	if w.registrant:
		try:
			data['registrantName'] = w.registrant.name
		except:
			pass

	# look for available emails.
	emails = {}
	contactEmail = w.contact_email
	if contactEmail:
		emails['contactEmail'] = contactEmail
	setEmail(emails, 'registrant', w.registrant)
	setEmail(emails, 'administrativeContact', w.administrative_contact)
	setEmail(emails, 'technicalContact', w.technical_contact)
	setEmail(emails, 'billingContact', w.billing_contact)
	setEmail(emails, 'zoneContact', w.zone_contact)
	data['emails'] = emails
	return data

def processYmlDomains(path:str):
	""" this function obtains the information from whoisxmlapi, for each domain present in the specified path file.
	the info will be stored in the global dictionary currentData.
	@param path: the yaml file with the domains list.
	"""
	d = loadYaml(path)	
	for k in d['domains']:
		currentData[k] = processDomain(k)

def checkUpdatedInfo(oldInfo, newInfo):
	""" this function compares the old and new information. If its different, then returns True.
	@param oldInfo: old information, typically the stored in SAVED_DATA_FILE
	@param newInfo: the new information, typically the provided by whoisxmlapi.
	@return: True if the new information is updated, False otherwise.
	"""
	# check all keys from newInfo compared with oldInfo keys.
	for k in newInfo:
		# ignore emails and registrantName keys, those shouldn't be checked.
		if k in ('emails', 'registrantName'): continue
		if oldInfo[k] != newInfo[k]: return True

	# the same as above but for emails.
	oldEmails = oldInfo['emails']
	newEmails = newInfo['emails']
	for k in newEmails:
		if k not in oldEmails: return True
		if oldEmails[k] != newEmails[k]: return True

	# since blank fields aren't registered, we need to check if some email address aren't present in the new information.
	for k in oldEmails:
		if k not in newEmails: return True
	return False

def runProcess():
	""" the main process of the script
	"""
	loadSettings()
	global yesterdayData
	# try to load the file with the old info, the first time the script is executed, this file doesn't exist.
	try:
		yesterdayData = loadPickle(SAVED_DATA_FILE)
	except:
		print('unable to load the saved data from yesterday')
	setWhoisClient()
	processYmlDomains(DOMAINS_LIST_FILE)

	# check if any domains information have been updated.
	for k in yesterdayData:
		if (k in currentData) and checkUpdatedInfo(yesterdayData[k], currentData[k]):
			updatedData[k] = currentData[k]

	if updatedData:
		sendMail("domains were updated!", 'See the info in the attached json', RECIPIENTS, updatedData)
	savePickle(currentData, SAVED_DATA_FILE)
	print ("Success!")

def sendMail(title, body, recipients, data = None, dataName = 'data.json'):
	""" sends an e-mail with the provided info.
	@param title: email Subject.
	@param body: email body.
	@param recipients: recipients email addresses.
	@param data: python object to be send in the e-mail as json format.
	@param dataName: the json file name to be attached in the email. It will contain the json data.
	"""
	msg = MIMEMultipart('alternative')
	msg['Subject'] = title
	msg['From'] = senderMail
	msg['To'] = ', '.join(recipients)
	msg.attach(MIMEText(body, 'plain'))
	if (data):
		attachment = MIMEText(json.dumps(data, default=str))
		attachment.add_header('Content-Disposition', 'attachment', filename=dataName)
		msg.attach(attachment)

	context = ssl.create_default_context()
	with smtplib.SMTP(smtpServer, smtpPort) as server:
		server.starttls(context=context)
		server.login(senderMail, senderPw)
		server.sendmail(senderMail, recipients, msg.as_string())

if __name__ == "__main__":
	runProcess()