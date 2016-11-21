import os
import re
import time
import json
import difflib
import httplib
from slackclient import SlackClient

# vdefine bot's ID
BOT_ID = 'U2FCRRL74'

# constants
AT_BOT = "<@" + BOT_ID + ">"
DEFINE = ('define', 'what is', 'explain', 'wtf is')
SETDEF = ('set definition for', 'set definition of', 'setdef', 'set')
IDENTIFY = ('identify', 'who is')
HELP = ('help', 'who are you', 'what are you', 'explain', 'what is your purpose')

# instantiate Slack client
# remember to "export SLACK_BOT_TOKEN={token}"
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def handle_command(command, channel, user):
	"""
		Receives commands directed at the bot and determines if they
		are valid commands. If so, then acts on the commands. If not,
		returns back what it needs for clarification.
	"""
	command = strip_emojis(command)
	response = ""
	attachments = [{}]
	default_response = "I don't know what {} is. Try using 'vdefine help'.".format(command)
	if command.startswith(DEFINE):
		query = retrieve_query_from_input(command, DEFINE)
		definition = get_definition(query)
		if definition:
			response = "The definition for *{}* is '{}'.".format(query, definition["definition"])
		else:
			possible_names = [f.replace(".json", "") for f in os.listdir('/db/teams/')]
			matches = get_close_matches(query, possible_names)
			if len(matches) > 1:
				response = "Couldn't find a definition for {}. Did you mean one of the following?:\n".format(query)
				for match in matches:
					definition = get_definition(match)
					response = response + "- *{}*: _{}_\n".format(definition["id"], definition["definition"])
			if len(matches) == 1:
				definition = get_definition(matches[0])
				response = "The definition for *{}* is '{}'.".format(definition["id"], definition["definition"])
			if len(matches) == 0:
				response = "I don't have a definition for {}!\n\nUse 'vdefine set definition for <word> as <definition>' to set one.".format(query)
	elif command.startswith(SETDEF):
		query = retrieve_query_from_input(command, SETDEF)
		q_elms = query.split(' as ', 1)
		if len(q_elms) < 2 or query.find(' as ') < 0:
			response = "Your syntax is messed up. Try 'vdefine set <word> as <definition>'."
		else:
			word = q_elms[0]
			defn = q_elms[1]
			response = "I'm setting the definition for *{}* as '{}'.".format(word, defn)
			set_definition(word, defn)
	elif command.startswith(IDENTIFY):
		query = retrieve_query_from_input(command, IDENTIFY)
		identification = get_identification(query)
		def _identify():
			attach = [{}]
			first_name = identification["name"].split(" ")[0]
			last_name = identification["name"].split(" ")[1]
			slack_id = get_user_slack_id(identification["slack"])
			resp = "{} is in {}.\n\n{}\n\nYou can find {} on slack at {}.".format(
				first_name,
				identification["type"],
				identification["bio"],
				first_name,
				slack_id)
			image_url = get_picture_url(first_name.lower(), last_name.lower())
			if image_url:
				attach = [{"title": first_name, "image_url": image_url, "color": "#3F9B5E"}]
			return resp, attach

		if identification:
			response, attachments = _identify()
		else:
			possible_names = [f.replace(".json", "") for f in os.listdir('/db/users/')]
			matches = get_close_matches(query, possible_names)
			if len(matches) > 1:
				response = "Found a few people with that name! Did you mean one of the following?:\n"
				for match in matches:
					id = get_identification(match)
					response = response + "- {} ({})\n".format(id["name"], id["type"])
			if len(matches) == 1:
				identification=get_identification(matches[0])
				response, attachments = _identify()
			if len(matches) == 0:
				response = "I don't know who {} is!".format(query)

	elif command.startswith(HELP):
		response = "I was created by Rameez and Levi with help from Cody, Corey, James and Nathan at Vendasta. \n\n" + \
		"*Usage*:\n- To lookup the definition of a word: 'vdefine define <word>', 'vdefine what is <word>', 'vdefine <word>'\n" + \
		"- To define or redefine a word: 'vdefine set <word> as <definition>', 'vdefine setdef <word> as <definition>'\n" + \
		"- To lookup an employee: 'vdefine who is <name>', 'vdefine identify <name>, 'vdefine <name>'\n" + \
		"- For this help dialog: 'vdefine help', 'vdefine explain', 'vdefine who are you', 'vdefine what are you'\n\n" +\
		"You can also PM me with your command, leaving out the 'vdefine'."

	if len(response) > 0:
		slack_client.api_call("chat.postMessage", channel=channel,
						  text=restore_emojis(response), attachments=json.dumps(attachments), as_user=True)
	elif not find_def_or_bio(command, channel, user) and response=="":
		slack_client.api_call("chat.postMessage", channel=channel,
						  text=default_response, attachments=json.dumps(attachments), as_user=True)


def strip_emojis(text):
	return re.sub(':([A-Za-z0-9\-]+):', '@%EM-\g<1>-@EM', text)

def restore_emojis(text):
	return re.sub('@%EM-([A-Za-z0-9\-]+)-@EM', ':\g<1>:', text)


def find_def_or_bio(command, channel, user):
	command = command.strip()
	command = re.sub('/']+', '', command)
	possible_names = [f.replace(".json", "") for f in os.listdir('/db/teams/')]
	matches = get_close_matches(command, possible_names)
	if len(matches) > 0:
		handle_command("what is {}".format(command), channel, user)
		return True
	possible_names = [f.replace(".json", "") for f in os.listdir('/db/users/')]
	matches = get_close_matches(command, possible_names)
	if command.replace(" ", "") in possible_names:
		matches = [command]
	if len(matches) > 0:
		handle_command("who is {}".format(command), channel, user)
		return True
	return False


def parse_slack_output(slack_rtm_output):
	"""
		The Slack Real Time Messaging API is an events firehose.
		this parsing function returns None unless a message is
		directed at the Bot, based on its ID.
	"""
	output_list = slack_rtm_output

	if output_list and len(output_list) > 0:
		for output in output_list:
			if output and 'text' in output and AT_BOT in output['text']:
				# return text after the @ mention, whitespace removed
				return output['text'].split(AT_BOT)[1].strip().lower(), \
					   output['channel'], output['user']
			elif output and 'text' in output and (output['text'].lower().find('vdefine') > -1) and not output['user'] == BOT_ID:
				# return text after vdefine, whitespace removed
				return re.compile(r"[vV][dD][eE][fF][iI][nN][eE]", flags=re.I).split(output['text'])[1].strip().lower(), \
					   output['channel'], output['user']
			elif output and 'text' in output and output['channel'] in get_dm_ids() and not output['user'] == BOT_ID:
				# direct message
				return output['text'].strip().lower(), output['channel'], output['user']
	return None, None, None

def get_close_matches(query, possible_names):
	matches = difflib.get_close_matches(query, possible_names)
	for name in possible_names:
		if (name.find(query) > -1) and name not in matches:
			matches = matches + [name]
	if len(matches) > 10:
		matches = matches[:10]
	return matches

def get_picture_url(first_name, last_name):

    def get_status_code(host, path="/"):
        try:
            conn = httplib.HTTPConnection(host)
            conn.request("HEAD", path)
            return conn.getresponse().status
        except StandardError:
            return None

    path = '/__v1404/static/images/team/{}-{}'.format(first_name, last_name)
    if get_status_code('www.vendasta.com', path+'.jpg') in (200, 302):
        return 'http://www.vendasta.com{}.jpg'.format(path)
    elif get_status_code('www.vendasta.com', path+'.jpeg') in (200, 302):
        return 'http://www.vendasta.com{}.jpeg'.format(path)
    elif get_status_code('www.vendasta.com', '/__v1404/static/images/team/{}{}.jpg'.format(first_name[0], last_name)) in (200, 302):
        return 'http://www.vendasta.com/__v1404/static/images/team/{}{}.jpg'.format(first_name[0], last_name)
    return None

def get_definition(query):
	query = query.lower()
	filename = "/db/teams/{}.json".format(query)
	if os.path.isfile(filename):
		with open(filename) as data_file:
			data = json.load(data_file)
		return data
	else:
		return False

def set_definition(word, definition):
	word = word.lower()
	filename = "/db/teams/{}.json".format(word)
	with open(filename, "w") as data_file:
		def_dict = {"id": word, "definition": definition}
		data_file.write(json.dumps(def_dict))
		print "definition written to {}".format(filename)
		return True
	return False

def get_identification(query):
	query = query.lower().replace(" ", "")
	filename = "/db/users/{}.json".format(query)
	if os.path.isfile(filename):
		with open(filename) as data_file:
			data = json.load(data_file)
		return data
	else:
		return False

def retrieve_query_from_input(input, commands_to_strip):
	input = re.sub('/', '', input)
	for item in commands_to_strip:
		if input.startswith(item):
			return input.replace(item, "", 1).strip()

def get_dm_ids():
	im_list = slack_client.api_call("im.list")
	bot_ims = []
	for im in im_list["ims"]:
		bot_ims = bot_ims + [im["id"]]
	return tuple(bot_ims)

def get_user_slack_id(slack_name):
	if slack_name.startswith('@'):
		slack_name = slack_name[1:]
	members = slack_client.api_call("users.list")["members"]
	for member in members:
		if member["name"] == slack_name:
			slack_name = "<@{}>".format(member["id"])
	if not slack_name.startswith(('<', '@')):
		slack_name = '@{}'.format(slack_name)
	return slack_name

if __name__ == "__main__":
	READ_WEBSOCKET_DELAY = 0.5 # 0.5 second delay between reading from firehose
	if slack_client.rtm_connect():
		print("vDefine connected and running!")
		while True:
			command, channel, user = parse_slack_output(slack_client.rtm_read())
			if command and channel:
				handle_command(command, channel, user)
				time.sleep(READ_WEBSOCKET_DELAY)
	else:
		print("Connection failed. Invalid Slack token or bot ID?")
