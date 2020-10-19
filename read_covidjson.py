import json
import pprint

import requests

url = "https://raw.githubusercontent.com/code4nagoya/covid19/master/data/data.json"
req = requests.get(url, timeout=15)

covid_dict = json.loads(req.text)

pprint.pprint(covid_dict["patients"]["data"][:10], width=40)