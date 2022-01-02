import logging
import time
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import json
import threading
from datetime import datetime

banned_ips = ['147.83.2.134', '147.83.2.135']
timestamp = 0
url = 'http://0.0.0.0:9200/_search'
content = {
  "query": {
    "bool": {
      "must": [
         {"match_phrase": {"flow.server.ip.addr": ["192.168.1.39"]}},
         {"range": {
           "@timestamp": {
             "gte": 1641122028632
              }
           }
         }
      ]
    }
  }
}
help_message = '''\
- help
- get_blacklist
- add_blacklist
- remove_blacklist
'''

# Telegram token
global token
token = "5089246815:AAHAtnr5iV8twx-rIFgrS4PCoHWZnyF9alg"

# Initialize logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


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


class BannedIPs:
    def __init__(self, initial):
        self.ips = set(initial)
        self.lock = threading.Lock()

    def add(self, ip):
        if not isValidIP(ip):
            raise ValueError(f'\"{ip}\" is not a valid ip')
        with self.lock:
            self.ips.add(ip)

    def remove(self, ip):
        with self.lock:
            self.ips.remove(ip)

    def get_list(self):
        with self.lock:
            return list(self.ips)


class AlertWorker(threading.Thread):
    def __init__(self, banned_ips: BannedIPs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.banned_ips = banned_ips

    def run(self):
        logger.info('Started ALERT thread')
        while True:
            try:
                response = self.send_request()
                self.handle_response(response)
            except ValueError:
                pass
            time.sleep(5)

    def send_request(self):
        timestamp = round((datetime.now().timestamp() - 60) * 1000)
        content['query']['bool']['must'][0]["match_phrase"]["flow.server.ip.addr"] = banned_ips
        #content['query']['bool']['must'][0]["match_phrase"]["flow.server.ip.addr"] =  self.banned_ips.get_list()
        content['query']['bool']['must'][1]['range']['@timestamp']['gte'] = timestamp
        response = requests.post(url, json=content)
        if response.status_code != 200:
            logger.warning(f'Elasticsearch request failed with code {response.status_code}')
            json_querry = json.dumps(content)
            logger.warning(json_querry)
            raise ValueError('Bad request')
        return json.loads(response.text)

    def handle_response(self, response):
        if response['hits']['total']['value'] > 0:
            print('Connection detected to UPC')
            self.send_telegram('Connection detected to UPC')

    def send_telegram(self, message: str):
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id="-624999628", text=msg)


class AddressListWorker(threading.Thread):
    def __init__(self, banned_ips: BannedIPs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.banned_ips = banned_ips
        self.updater = Updater(token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_handler(CommandHandler("help", self.get_help))
        self.dispatcher.add_handler(CommandHandler("get_blacklist", self.get_blacklist))
        self.dispatcher.add_handler(CommandHandler("add_blacklist", self.add_blacklist))
        self.dispatcher.add_handler(CommandHandler("remove_blacklist", self.remove_blacklist))
        self.dispatcher.add_error_handler(self.error)

    def run(self):
        logger.info('Started LIST thread')
        self.updater.start_polling()
        self.updater.idle()

    def get_help(self, update, context):
        update.message.reply_text(help_message)

    def get_blacklist(self, update, context):
        ip_list = self.banned_ips.get_list()
        ip_str = map(lambda s: f'  - {s}', self.banned_ips)
        ip_str = '\n'.join(ip_str)
        update.message.reply_text(f'Banned IPs:\n{ip_str}')

    def add_blacklist(self, update, context):
        try:
            ip = context.args[0]
            self.banned_ips.add(ip)
            update.message.reply_text(f'Added {ip} to banned IPs.')
        except(IndexError, ValueError):
            update.message.reply_text('/add_to_blacklist <Add a valid IP>')

    def remove_blacklist(self):
        try:
            ip = context.args[0]
            banned_ips.remove(ip)
            update.message.reply_text(f'Removed {ip} from banned IPs.')
        except(IndexError, ValueError):
            update.message.reply_text('/remove_from_blacklist <Add a valid IP>')

    def error(self, update, context):
        logger.error(f'Update \"{update}\" caused error \"{context.error}\"')
        logger.error('Update services may be down')


if __name__ == '__main__':
    banned = BannedIPs(banned_ips)
    alert_worker = AlertWorker(banned, daemon=True)
    address_worker = AddressListWorker(banned, daemon=True)
    alert_worker.start()
    address_worker.run()
