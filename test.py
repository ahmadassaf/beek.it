import requests

SERVER = 'http://127.0.0.1:5000/api/addUrl'

payload = {'url': 'http://vimeo.com/18150336'}
r = requests.get(SERVER, params=payload)
print r

payload = {'url': 'http://edition.cnn.com/2014/10/10/opinion/whiton-kim-missing/index.html?hpt=hp_c1'}
r = requests.get(SERVER, params=payload)
print r
