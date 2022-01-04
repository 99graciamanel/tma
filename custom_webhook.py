import logging
import ipaddress
import time
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import json
import threading
import socket
from datetime import datetime

banned_ips = ['147.83.2.134', '147.83.2.135']
timestamp = 0
url = 'http://0.0.0.0:9200/elastiflow*/'
help_message = '''\
- help
- get_blacklist
- add_blacklist
- remove_blacklist
'''
alert_message = '''\
Detected security event {flow_id}:
- Exporter: {exporter}
- Source: {src}
- Source port: {src_p}
- Destination: {dst}
- Destination port: {dst_p}
'''

# Telegram token
global token
token = "5089246815:AAHAtnr5iV8twx-rIFgrS4PCoHWZnyF9alg"

# Initialize logger
logging.basicConfig(format='%(threadName)s:%(name)s:%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class BannedIPs:
    def __init__(self, initial):
        self.ips = set(initial)
        self.lock = threading.Lock()

    def add(self, ip):
        ip = ipaddress.ip_address(ip)
        with self.lock:
            self.ips.add(str(ip))

    def remove(self, ip):
        with self.lock:
            self.ips.remove(ip)

    def get_list(self):
        with self.lock:
            return list(self.ips)


class BlacklistAlertWorker(threading.Thread):
    def __init__(self, banned_ips: BannedIPs, *args, **kwargs):
        super().__init__(name='BLThread', *args, **kwargs)
        self.banned_ips = banned_ips
        self.url = "%s%s" % (url, '_search')
        self.content = {
          "query": {
            "bool": {
              "filter": [
                {"range": { "@timestamp": {"gte": 1618871111000}}}
              ],
              "should": [
                {"term": { "flow.server.ip.addr": "147.83.2.134"}},
                {"term": { "flow.server.ip.addr": "147.83.2.135"}},
              ],
              "minimum_should_match": 1
            }
          }
        }
        self.registered_events = set()

    def run(self):
        logger.info('Started Blacklist ALERT thread')
        while True:
            try:
                response = self.send_request()
                self.handle_response(response)
            except ValueError:
                pass
            time.sleep(5)

    def get_rules(self):
        self.content['query']['bool']['should'] = []
        for ip in self.banned_ips.get_list():
            self.content['query']['bool']['should'].append({"term": { "flow.server.ip.addr": ip}})
        self.content['query']['bool']['must_not'] = []
        for event in self.registered_events:
            self.content['query']['bool']['must_not'].append({"term": { "_id": event}})

    def get_timestamp(self):
        timestamp = round((datetime.now().timestamp() - 60) * 1000)
        self.content['query']['bool']['filter'][0]['range']['@timestamp']['gte'] = timestamp

    def send_request(self):
        self.get_rules()
        self.get_timestamp()
        response = requests.post(self.url, json=self.content)
        if response.status_code != 200:
            logger.warning(f'Elasticsearch request failed with code {response.status_code}')
            json_querry = json.dumps(self.content)
            logger.warning(json_querry)
            raise ValueError('Bad request')
        return json.loads(response.text)

    def get_short_message(self, hit):
        flow = hit['_source']['flow']
        src = flow['client']['ip']['addr']
        dst = flow['server']['ip']['addr']
        return f'Connection detected form {src} to {dst}'

    def get_message(self, hit):
        flow = hit['_source']['flow']
        data = {
            'flow_id': hit['_id'],
            'src': flow['client']['ip']['addr'],
            'src_p': flow['client']['l4']['port']['name'],
            'dst': flow['server']['ip']['addr'],
            'dst_p': flow['server']['l4']['port']['name'],
            'exporter': flow['export']['ip']['addr']
        }
        return alert_message.format(**data)

    def register_event(self, hit):
        self.registered_events.add(hit['_id'])

    def handle_response(self, response):
        if response['hits']['total']['value'] > 0:
            for hit in response['hits']['hits']:
                self.send_telegram(self.get_message(hit))
                logger.info(self.get_short_message(hit))
                self.register_event(hit)
        else:
            logger.info('Everything is fine.')

    def send_telegram(self, message: str):
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id="-624999628", text=message)


class DDoSAlertWorker(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(name='DDosThread', *args, **kwargs)
        self.url = "%s%s" % (url, '_count')
        self.content = {
          "query": {
            "bool": {
              "filter": [
                {"range": { "@timestamp": {"gte": 1618871111000}}}
              ],
              "should": [
                {"term": { "flow.server.ip.addr": "192.168.1.0/24"}},
              ],
              "minimum_should_match": 1
            }
          }
        }

    def run(self):
        logger.info('Started DDoS ALERT thread')
        while True:
            try:
                response = self.send_request()
                self.handle_response(response)
            except ValueError:
                pass
            time.sleep(5)

    def get_timestamp(self):
        timestamp = round((datetime.now().timestamp() - 60) * 1000)
        self.content['query']['bool']['filter'][0]['range']['@timestamp']['gte'] = timestamp

    def send_request(self):
        self.get_timestamp()
        response = requests.post(self.url, json=self.content)
        if response.status_code != 200:
            logger.warning(f'Elasticsearch request failed with code {response.status_code}')
            json_querry = json.dumps(self.content)
            logger.warning(json_querry)
            raise ValueError('Bad request')
        return json.loads(response.text)

    def handle_response(self, response):
        if response['count'] > 100:
            print('DDoS found for our servers')
            self.send_telegram('DDoS found for our servers')
            self.sleep_ddos_alerts()

    def send_telegram(self, message: str):
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id="-624999628", text=message)

    def sleep_ddos_alerts(self):
        time.sleep(60)


class AddressListWorker(threading.Thread):
    def __init__(self, banned_ips: BannedIPs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.banned_ips = banned_ips
        self.updater = Updater(token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_handler(CommandHandler("help", self.get_help))
        self.dispatcher.add_handler(CommandHandler("get_blacklist", self.get_blacklist))
        self.dispatcher.add_handler(CommandHandler("add_blacklist", self.add_blacklist))
        self.dispatcher.add_handler(CommandHandler("add_domain", self.add_domain))
        self.dispatcher.add_handler(CommandHandler("remove_blacklist", self.remove_blacklist))
        self.dispatcher.add_error_handler(self.error)

    def run(self):
        logger.info('Started LIST thread')
        self.updater.start_polling()
        self.updater.idle()

    def get_help(self, update, context):
        update.message.reply_text(help_message)
        logger.info('Showed help message')

    def get_blacklist(self, update, context):
        ip_list = self.banned_ips.get_list()
        ip_str = map(lambda s: f'  - {s}', ip_list)
        ip_str = '\n'.join(ip_str)
        update.message.reply_text(f'Banned IPs:\n{ip_str}')
        logger.info('Showed IP list')

    def add_blacklist(self, update, context):
        try:
            ip = context.args[0]
            self.banned_ips.add(ip)
            update.message.reply_text(f'Added {ip} to banned IPs.')
            logger.info(f'Added {ip} to banned IPs.')
        except(IndexError, ValueError):
            update.message.reply_text('/add_blacklist <Add a valid IP>')

    def remove_blacklist(self, update, context):
        try:
            ip = context.args[0]
            self.banned_ips.remove(ip)
            update.message.reply_text(f'Removed {ip} from banned IPs.')
            logger.info(f'Removed {ip} from banned IPs.')
        except(IndexError, ValueError):
            update.message.reply_text('/remove_blacklist <Add a valid IP>')

    def add_domain(self, update, context):
        try:
            hostname, aliaslist, ipaddrlist = socket.gethostbyname_ex(context.args[0])
            for ip in ipaddrlist:
                self.banned_ips.add(ip)
                update.message.reply_text(f'Added {ip} to banned IPs.')
                logger.info(f'Added {ip} to banned IPs.')
        except Exception:
            update.message.reply_text('/add_domain <Add a valid domain>')

    def error(self, update, context):
        logger.error(f'Update \"{update}\" caused error \"{context.error}\".')
        logger.error('Update services may be down.')


if __name__ == '__main__':
    banned = BannedIPs(banned_ips)
    blacklist_worker = BlacklistAlertWorker(banned, daemon=True)
    ddos_worker = DDoSAlertWorker(daemon=True)
    address_worker = AddressListWorker(banned, daemon=True)
    blacklist_worker.start()
    ddos_worker.start()
    address_worker.run()
