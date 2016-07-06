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

var controller = Botkit.slackbot({
    debug: false,
    json_file_store: '/db/vdefine'
})

var bot = controller.spawn({
    token: process.env.token
}).startRTM();

controller.hears(['what is (.*)', 'what does (.*) mean', '^define (.*)', 'wtf is (.*)', 'what are (.*)'], 'direct_message,direct_mention,mention', function(bot, message){define(bot, message)});

controller.hears(['redefine (.*)'], 'direct_message,direct_mention,mention', function(bot, message) {
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
				        	pattern: 'yes',
					           callback: function(response, convo) {
					           	   convo.ask('Okay, what would you like to define it as?', function(response, convo) {
					           	   	   if (def) {
					           	   	   	   def = {
					           	   	   	   	   id: lookup
										   }
					           	   	   	   def.definition = response.text;
					           	   	   	   controller.storage.teams.save(def, function(err, id) {
					           	   	   	   	   bot.reply(message, 'Got it, I\'ve defined '+lookup+'.');
					           	   	   	   	   convo.next();
					           	   	   	   });
					           	   	   }
					           	   });
					           	   convo.next();
					           }
					    },
					    {
					    	pattern: 'no',
					    	callback: function(response, convo) {
					    		convo.say('Okay, I won\'t.');
					    		convo.next();
					    	}
					    },
					    {
					    	default: true,
					    	callback: function(response, convo) {
					    		convo.repeat();
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

controller.hears(['uptime', 'identify yourself', 'who are you', 'what is your name'],
    'direct_message,direct_mention,mention', function(bot, message) {

        var hostname = os.hostname();
        var uptime = formatUptime(process.uptime());

        bot.reply(message,
            ':robot_face: I am a bot named <@' + bot.identity.name +
             '>. I have been running for ' + uptime + ' on ' + hostname + '.');

    });

function formatUptime(uptime) {
    var unit = 'second';
    if (uptime > 60) {
        uptime = uptime / 60;
        unit = 'minute';
    }
    if (uptime > 60) {
        uptime = uptime / 60;
        unit = 'hour';
    }
    if (uptime != 1) {
        unit = unit + 's';
    }

    uptime = uptime + ' ' + unit;
    return uptime;
}

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
							pattern: 'yes',
							callback: function(response, convo) {
								convo.ask('Okay, what would you like to define it as?', function(response, convo) {
									if (!def) {
										def = {
											id: lookup
										}
										def.definition = response.text;
										controller.storage.teams.save(def, function(err, id) {
											bot.reply(message, 'Got it, I\'ve defined '+lookup+'.');
											convo.next();
										});
									}

								});
								
								convo.next();
							}
						},
						{
							pattern: 'no',
							callback: function(response, convo) {
								convo.say('Okay, I won\'t.');
								convo.next();
							}
						},
						{
							default: true,
							callback: function(response, convo) {
								convo.repeat();
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
