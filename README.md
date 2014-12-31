## What is this

See intro for project here https://github.com/stbd/walvomo-server

This is the ugly sibling of walvomo-server, it includes various scripts that fetch vote data and RSS feeds from web, convert them to Protocol Buffers objects (defined in walvomo-server/src/db/*.proto), and finally push them to Couchbase database used by walvomo-server. Scripts assume that walvomo-server can be found from parent folder (i.e. ../walvomo-server).

As said, most of this stuff is not pretty, they are written hastily, goal being only to get them to work. Some excuses' are that this wasn't the interesting part of the project, also I had lot of trouble parsing the vote data from Eduskunta website as, at least at the time, the HTML wasn't perfect. I wasn't for example able to get any of the Python HTML parsers to work out of the box, that is why bot.py actually parses the page by hand. Take a look if you have the courage (I recommend not doing it just before going to bed as it might cause nightmares).

## Why is this here

Well, it is the other half of walvomo-server, without these the project is quite useless. I also think the everything should still work, only thing needed would be to configure seating for member of parliament.

## How to use

Well...

You would first need to configure seating with generateSeatingInfo.py, this takes csv file as parameter (if someone is really interested I can try to add an example). Then configure some information about electoral period, and then in theory update_data.sh could be configured  (for example with cron) to update data every once in awhile.

## Do they really work?

Believe it or not, the scripts did run for a few years without any problems, the only manual step was to update seats when seats changed, otherwise cron did all the work.

## What's missing

I removed all configurations seat data as they were outdated.
