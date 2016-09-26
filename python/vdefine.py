import os
import re
import time
import json
import difflib
from slackclient import SlackClient

# vdefine bot's ID as an environment variable
BOT_ID = 'U2FCRRL74'

# constants
AT_BOT = "<@" + BOT_ID + ">"
DEFINE = ('define', 'what is', 'explain', 'wtf is')
REDEFINE = ('redefine', 'set definition for')
IDENTIFY = ('identify', 'who is')
HELP = ('help', 'who are you', 'what are you', 'explain')

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def handle_command(command, channel, user):
	"""
		Receives commands directed at the bot and determines if they
		are valid commands. If so, then acts on the commands. If not,
		returns back what it needs for clarification.
	"""
	response = "I don't know what you mean and I won't respond to it.".format(command)
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
					response = response + "- *{}*: ({})\n".format(definition["id"], definition["definition"])
			if len(matches) == 1:
				definition = get_definition(matches[0])
				response = "The definition for *{}* is '{}'.".format(definition["id"], definition["definition"])
			if len(matches) == 0:
				response = "I don't have a definition for {}!\n\nWould you like to be the first to define it?".format(query)

	if command.startswith(REDEFINE):
		query = retrieve_query_from_input(command, REDEFINE)
		definition = get_definition(query)
		if definition:
			response = "{} is already defined as {}. Would you like to change this?".format(query, definition)
		else:
			response = "What would you like to define {} as?".format(query)
	if command.startswith(IDENTIFY):

		def _identify():
			first_name = identification["name"].split(" ")[0]
			slack_id = get_user_slack_id(identification["slack"])
			return "{} is in {}.\n\n{}\n\nYou can find {} on slack at {}.".format(
				first_name,
				identification["type"],
				identification["bio"], 
				first_name,
				slack_id)

		query = retrieve_query_from_input(command, IDENTIFY)
		identification = get_identification(query)
		if identification:
			response = _identify()
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
				response = _identify()
			if len(matches) == 0:
				response = "I don't know who {} is!".format(query)

	if command.startswith(HELP):
		response = "I was created by Rameez, Levi, Cody, Corey, James, and Nathan at Vendasta.\n\nYou " + \
		"can ask me to define a Vendasta-specific word or acronym, and you can provide a definition if there isn't one. " + \
		"Just start your post with \"@vdefine what is...\"\n\n" + \
		"You can also ask me to give you more information about any Vendasta employee. Start your post with \"@vdefine who is...\"\n\n" + \
		"If you want to get a definition in private, just send me a Direct Message."
	slack_client.api_call("chat.postMessage", channel=channel,
						  text=response, as_user=True)


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
			elif output and 'text' in output and (output['text'].find('vdefine') > -1):
				# return text after vdefine, whitespace removed
				return output['text'].split('vdefine')[1].strip().lower(), \
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
	return matches

def get_definition(query):
	query = query.lower()
	filename = "/db/teams/{}.json".format(query)
	if os.path.isfile(filename):
		with open(filename) as data_file:
			data = json.load(data_file)
		return data
	else:
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
	input = re.sub('[^A-Za-z0-9\ ]+', '', input)
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