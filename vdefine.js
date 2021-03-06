/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Get a Bot token from Slack:
    -> http://my.slack.com/services/new/bot
  Run your bot from the command line:
    token=<MY TOKEN> node slack_bot.js
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/


if (!process.env.token) {
    console.log('Error: Specify token in environment');
    process.exit(1);
}

var Botkit = require('./node_modules/botkit/lib/Botkit.js');
var os = require('os');

var delay = 500;

var controller = Botkit.slackbot({
    debug: false,
    json_file_store: '/db/'
});

var bot = controller.spawn({
    token: process.env.token
}).startRTM();

controller.hears(['identify yourself', 'who are you', 'what is your name', 'help','introduce yourself'],
    'direct_message,direct_mention,mention', function(bot, message) {

        bot.reply(message,
            'This bot was created by Rameez, Levi, Cody, Corey, James, and Nathan at Vendasta.\n' +
			'You can ask it to define a Vendasta-specific word or acronym, and you can provide a definition if there isn\'t one. ' +
			'Just start your post with "@vdefine what is..."\n' +
			'You can also ask it to give you more information about any Vendasta employee. Start your post with "@vdefine who is..."\n'+
			'If you want to get a definition in private, just sent it a Direct Message.')
    });


controller.hears(['redefine (.*)', '.* redefine (.*)', '.* redefine (.*) to .*'], 'direct_message,direct_mention,mention', function(bot, message) {
	var lookup = message.match[1];
	lookup = lookup.replace(/[^\w\s]|_/g, "").replace(/\s+/g, " ").toLowerCase();

	controller.storage.teams.get(lookup, function(err, def) {
		if (!def) {
		     bot.reply(message, 'There is no definition for ' + lookup + '!');
		} else {
			bot.startConversation(message, function(err, convo) {
			    if (!err) {
              		convo.ask('Want to redefine ' + lookup + '?', [
	         		    {
				        	pattern: bot.utterances.yes,
					           callback: function(response, convo) {
					           	   convo.ask('Okay, what would you like to define it as?', function(response, convo) {
					           	   	   if (def) {
					           	   	   	   def = {
					           	   	   	   	   id: lookup
										   };

										   var text = response.text;

										   var regex=/(.*)<(.+)>(.*)/g;

										   while (regex.exec(text)) {
										   	   	text = text.replace(regex, "\$1\$2\$3");
										   }

					           	   	   	   def.definition = text;
					           	   	   	   controller.storage.teams.save(def, function(err, id) {
						           	   	   	   	setTimeout(function() {
	  												bot.reply(message, 'Got it, I\'ve defined '+lookup+'.');
					           	   	   	   	   		convo.next();
												}, delay);
					           	   	   	   });
					           	   	   }
					           	   });
					           	   convo.next();
					           }
					    },
					    {
					    	pattern: bot.utterances.no,
					    	callback: function(response, convo) {
					    		convo.say('Okay, I won\'t.');
					    		convo.next();
					    	}
					    },
					    {
					    	default: true,
					    	callback: function(response, convo) {
					    		convo.say('I have no idea what you\'re talking about, and I won\'t respond to it.');
					    		convo.next();
					    	}
					    }
					]);
					convo.on('end', function(convo) {
						bot.reply(message, "Bye!");
					});
				}
			});
		}
	});
});

controller.hears(['who is (.*)', 'who\'s (.*)', 'who (.*)', 'get me (.*)'], 'direct_message,direct_mention,mention', function(bot, message){
	var lookup = message.match[1];
	lookup = lookup.replace(/\s+|_/g, "").toLowerCase();

	controller.storage.users.get(lookup, function(err, person) {
		if (!person) {
			bot.reply(message, 'I don\'t know who ' + message.match[1] + ' is!');
			controller.storage.users.all(function(err, people) {
				var listOfPeople = "";
				people.forEach(function(po) {
					if (po.name.toLowerCase().indexOf(lookup) > -1) {
						listOfPeople += "- " + po.name + "\n";
					}
				});
				if (listOfPeople.length > 0) {
					bot.reply(message, 'You may have meant one of the following people:');
					bot.reply(message, listOfPeople);
				} else {
					bot.reply(message, "Check your spelling, I'm not that smart yet.")
				}
			})
		} else {
			bot.reply(message, person.name + ' is in ' + person.type + '. ' + person.bio +
				' If you want to get a hold of ' + person.name.split(" ")[0] + ', use the Slack name ' + person.slack + '.');
		}
	})
});

controller.hears(['what is (.*)', 'what does (.*) mean', '^define (.*)', 'wtf is (.*)', 'what are (.*)', '(.*)'], 'direct_message,direct_mention,mention', function(bot, message){define(bot, message)});

function define(bot, message) {
	var lookup = message.match[1];
	lookup = lookup.replace(/[^\w\s]|_/g, "").replace(/\s+/g, " ").toLowerCase();

	controller.storage.teams.get(lookup, function(err, def) {
		if (!def) {
			bot.reply(message, 'There is no definition for ' + lookup + '!');
			bot.startConversation(message, function(err, convo) {
				if (!err) {
					convo.ask('Want to define ' + lookup + '?', [
						{
							pattern: bot.utterances.yes,
							callback: function(response, convo) {
								convo.ask('Okay, what would you like to define it as?', function(response, convo) {
									if (!def) {
										def = {
											id: lookup
										};
			
										var text = response.text;
			                            var regex=/(.*)<(.+)>(.*)/g;
								
										while (regex.exec(text)) {
											text = text.replace(regex, "\$1\$2\$3");
										}

										def.definition = text;
										controller.storage.teams.save(def, function(err, id) {
											setTimeout(function() {
  												bot.reply(message, 'Got it, I\'ve defined '+lookup+'.');
  												convo.next();
											}, delay);

										});
									}

								});
								
								convo.next();
							}
						},
						{
							pattern: bot.utterances.no,
							callback: function(response, convo) {
								convo.say('Okay, I won\'t.');
								convo.next();
							}
						},
						{
							default: true,
							callback: function(response, convo) {
								convo.say('I have no idea what you said, and I won\'t respond to it.');
								convo.next();
							}
						}
					]);
					convo.on('end', function(convo) {
						bot.reply(message, "Bye!");
					});
				}
			});
		} else {
			bot.reply(message, 'The definition of "' + lookup + '" is "' + def.definition + '".'); }
	});
}
