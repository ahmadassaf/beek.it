# coding: utf-8

"""
A microservice, that takes an URL and saves the url in some database.
"""

from flask import Flask, request, abort, jsonify, g
from porc import Client
import datetime
import embedly
import hashlib
import json
import nltk
import os
import requests
import uuid

# embedly
embedly_client = embedly.Embedly(os.environ['EMBEDLY_API_KEY'])

# orchestrate.io - data storage pluse search
client = Client(os.environ['ORCHESTRATE_API_KEY'])

client.ping().raise_for_status()

app = Flask(__name__)

def alchemy_call(service, params):
    ALCHEMY_URL = "http://access.alchemyapi.com/calls/url/"

    params['outputMode'] = 'json'
    params['apikey'] = os.environ['ALCHEMY_API_KEY']
    r = requests.get(ALCHEMY_URL + service, params=params)
    app.logger.debug('json', r.text)
    return json.loads(r.text)

def alchemy_flow(url):
    #extract category
    response = alchemy_call('URLGetCategory', {'url':url} )
    category = response.get('category', [])
    app.logger.debug('category', category)

    #extract full text text
    response = alchemy_call('URLGetRawText', {'url':url} )
    text = response.get('text', '')
    app.logger.debug('text', text)

    if text:
        #extract keywords
        keywords_params = {'sentiment':0, 'keywordExtractMode': 'strict', 'maxRetrieve': 10, 'url': url}
        keywords = alchemy_call('URLGetRankedKeywords', keywords_params ).get('keywords', [])
        app.logger.debug('keywords', keywords)
    else:
        keywords = []

    return {
        'category': category,
        'text': text,
        'keywords': keywords,
    }

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route("/api/addUrl")
def add_url():
    url = request.args.get('url')
    if not url:
        return jsonify(msg='no url supplied')

    id = None
    app.logger.debug('searching orchestrate.io...')
    pages = client.search('page.v1', 'url:"%s"' % url)
    page = pages.next()

    if len(page['results']) == 0:
        app.logger.debug('no such page or collection, generating key')
        id = str(uuid.uuid4())
    else:
        try:
            page.raise_for_status()
        except requests.exceptions.HTTPError as err:
            app.logger.debug(err)
            id = str(uuid.uuid4())
        else:
            # reuse the ID
            app.logger.debug('page exists')
            if len(page['results']) > 1:
                app.logger.warn('more than one document with the same id')
            id = page['results'][0]['path']['key']

    if id is None:
        abort(500)

    # redownload the page - we could spare that for now
    r = requests.get(url)
    html = r.text

    embedly_data = {}
    alchemy_data = {}

    if embedly_client.is_supported(url):
        embedly_response = embedly_client.oembed(url)
        embedly_data = embedly_response.__dict__
        app.logger.debug('EMBEDLY >>>\n%s' % embedly_data)
    else:
        app.logger.debug('ALCHEMY >>>')
        alchemy_data = alchemy_flow(url)

    response = client.put('page.v1', id, {
        'html': html,
        'url': url,
        'datetime': datetime.datetime.utcnow().strftime("%s"),
        # add api results here ...
        'embedly': embedly_data,
        'alchemy': alchemy_data,
    })
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        return jsonify(msg=str(err))
    return jsonify(msg="ok", url=url, id=id)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
