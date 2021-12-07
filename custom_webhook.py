import requests
import json
import time

url = 'http://0.0.0.0:9200/_search'
content = {
  "query": {
    "bool": {
      "must": [
         {"match_phrase": {"flow.export.host.name":  "192.168.1.200"}},
         {"match_phrase": {"flow.server.ip.addr":  "147.83.2.135"}}
      ]
    }
  }
}

while True:
    response = requests.post(url, json=content)
    response_data = json.loads(response.text)
    if response_data['hits']['total']['value'] > 0:
        print('Connection detected to UPC')
    time.sleep(1)
