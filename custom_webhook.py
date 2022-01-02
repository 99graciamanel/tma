import logging

import time
import telegram
import requests
import json
from datetime import datetime

exporter_ip = '192.168.1.39'
banned_ip = '147.83.2.135'
timestamp = 0

url = 'http://0.0.0.0:9200/_search'
content = {
  "query": {
    "bool": {
      "must": [
         {"match_phrase": {"flow.export.host.name":  exporter_ip}},
         {"match_phrase": {"flow.server.ip.addr": banned_ip}},
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

def send(msg):
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id="-624999628", text=msg)

if __name__ == '__main__':
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
