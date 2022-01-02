import logging

import time
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import requests
import json
from datetime import datetime

exporter_ip = '192.168.1.39'
banned_ips = set(['147.83.2.135'])
timestamp = 0

url = 'http://0.0.0.0:9200/_search'
content = {
  "query": {
    "bool": {
      "must": [
         {"match_phrase": {"flow.export.host.name": exporter_ip}},
         {"match_phrase": {"flow.server.ip.addr": banned_ips}},
         {"range": {
           "@timestamp": {
             "gte": timestamp
              }
           }
         }
      ]
    }
  }
}

# Enable logging:
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

global token
token = "5089246815:AAHAtnr5iV8twx-rIFgrS4PCoHWZnyF9alg"

def addToBlacklist(update, context):
    try:
        ip = context.args[0]
        if not isValidIP(ip):
            update.message.reply_text("Not valid IP")
            return
        banned_ips.add(ip)
        content['query']['bool']['must'][0]['match_phrase']['flow.export.host.name'] = banned_ips
        update.message.reply_text("Added to banned IPs. Current list.")
    except(IndexError, ValueError):
        update.message.reply_text('/add_to_blacklist <Add a valid IP>')

def removeFromBlacklist(update, context):
    update.message.reply_text("Work in progress")

def help(update, context):
    update.message.reply_text(" \
        - help\n\
        - add_to_blacklist\n\
        - remove_from_blacklist\n\
" )


def isValidIP(ip):
    parts = ip.split(".")
    if len(parts) != 4:
        return False

    for part in parts:
        if not isinstance(int(part), int):
            return False

        if int(part) < 0 or int(part) > 255:
            return False

    return True

def error(update, context): # Funcio per defecte del bot
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def send(msg):
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id="-624999628", text=msg)

if __name__ == '__main__':

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("add_to_blacklist", addToBlacklist))
    dp.add_handler(CommandHandler("remove_from_blacklist", removeFromBlacklist))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

    while True:
        timestamp = round((datetime.now().timestamp() - 60) * 1000)
        print(timestamp)

        content['query']['bool']['must'][2]['range']['@timestamp']['gte'] = timestamp
        print(content)

        response = requests.post(url, json=content)
        response_data = json.loads(response.text)

        print(response_data)
        if response_data['hits']['total']['value'] > 0:
            print('Connection detected to UPC')
            send('Connection detected to UPC')
        time.sleep(5)
