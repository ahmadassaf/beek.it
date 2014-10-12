#!/usr/bin/env python
# coding: utf-8

"""
Various jobs during ingesting.
"""

from utils import url_to_doc_id
import datetime
import elasticsearch
import embedly
import json
import os
import requests

def index(url):
    """ Index a URL into elasticsearch. """
    resp = requests.get(url)
    es = elasticsearch.Elasticsearch()
    es.index(index='beek', doc_type='page', id=url_to_doc_id(url), body={
        'url': url,
        'content': resp.text,
        'date': datetime.datetime.now(),
    }, refresh=True)

def count_words(id):
    """ Count the words in doc and update the document. """
    es = elasticsearch.Elasticsearch()
    source = es.get_source(index='beek', doc_type='page', id=id)
    count = len(source['content'].split())
    es.update(index='beek', doc_type='page', id=id,
              body={'doc': {'count': count}}, refresh=True)


def alchemy_call(service, params):
    """ Helper for alchemy_flow. """
    ALCHEMY_URL = "http://access.alchemyapi.com/calls/url/"

    params['outputMode'] = 'json'
    params['apikey'] = os.environ['ALCHEMY_API_KEY']
    r = requests.get(ALCHEMY_URL + service, params=params)
    return json.loads(r.text)

def alchemy_call_data(service, params):
    """ Helper for alchemy_flow. """
    ALCHEMY_URL = "http://access.alchemyapi.com/calls/text/"

    params['outputMode'] = 'json'
    params['apikey'] = os.environ['ALCHEMY_API_KEY']
    print params['apikey']
    r = requests.get(ALCHEMY_URL + service, params=params)
    print 'RRRR', r.__dict__
    return json.loads(r.text)

def process_evernote(token):
    import our_evernote
    from evernote.edam.notestore import NoteStore
    import evernote.edam.type.ttypes as Types
    token = 'S=s1:U=8fa64:E=1505674a78d:C=148fec37b28:P=1cd:A=en-devtoken:V=2:H=557207e871d827a672dd55ffdb6b0a11'
    note_store, urls_and_contents = our_evernote.get_source_urls(token)
    es = elasticsearch.Elasticsearch()


    tags = dict( (tag.name, tag) for tag in note_store.listTags(token))

    for url, note in urls_and_contents:
        content = note.content
        response = alchemy_call_data('TextGetCategory', {'text':content} )
        print(response)
        category = response.get('category', [])
        tag = tags.get(category)
        if not tag:
            tag_data = Types.Tag(name=category)
            tag = note_store.createTag(token, tag_data)

        if tag.guid not in note.tagGuids:
            note.tagGuids.append(tag.guid)
            note_store.updateNote(token, note)

        es.index(index='beek', doc_type='page', id=url_to_doc_id(url), body={
            'url': url,
            'category': category,
            'text': content,
            'content': content,
            'date': datetime.datetime.now(),
        }, refresh=True)

def query_alchemy(url):
    """ Ask alchemy. Store alchemy results in a separate doc_type. """    
    response = alchemy_call('URLGetCategory', {'url':url} )
    print(response)
    category = response.get('category', [])

    response = alchemy_call('URLGetLanguage', {'url':url} )
    print(response)
    language = response.get('language', [])

    response = alchemy_call('URLGetRankedNamedEntities', {'url':url} )
    print(response)
    entities = response.get('entities', [])

    # some finer grained entities
    locations = [e['text'] for e in entities if e['type'] in ('City', 'Country',
                                                              'GeographicFeature', 'Region', 'Continent')]
    actors = [e['text'] for e in entities if e['type'] in ('Person', 'Organization', 'Company')]
    terminology = [e['text'] for e in entities if e['type'] in ('FieldTerminology')]

    for e in entities:
        if e['type'] not in ('City', 'Country', 'Person', 'Organization'):
            print(e)

    # extract full text text
    response = alchemy_call('URLGetRawText', {'url':url} )
    print(response)
    text = response.get('text', '')

    if text:
        # extract keywords
        keywords_params = {'sentiment': 1, 'keywordExtractMode': 'strict', 'maxRetrieve': 10, 'url': url}
        keywords = alchemy_call('URLGetRankedKeywords', keywords_params ).get('keywords', [])
    else:
        keywords = []

    actors_joined = [actor.replace(' ', '_') for actor in actors]

    es = elasticsearch.Elasticsearch()
    es.update(index='beek', doc_type='page', id=url_to_doc_id(url),
              body={'doc': {'category': category,
                            'text': text,
                            'keywords': keywords,
                            'language': language,
                            'entities': entities,
                            'locations': locations,
                            'actors': actors,
                            'actors_joined': actors_joined,
                            'terminology': terminology}}, refresh=True)

def query_embedly(url):
    """ Get embedly, if available, store it in a separate doc_type. """
    client = embedly.Embedly(os.environ['EMBEDLY_API_KEY'])
    #if client.is_supported(url):
    resp = client.oembed(url)
    data = resp.__dict__        
    es = elasticsearch.Elasticsearch()
    es.update(index='beek', doc_type='page', id=url_to_doc_id(url), body={'doc': {'embedly': data}})



def get_terms_images():
    """ Try to fetch the depictions of terms from dbpedia and cache the
        URL locally for faster access. """
    r = requests.get('http://localhost:5000/terms')
    if r.status_code >= 400:
        raise RuntimeError('we need /terms')
    terms = json.loads(r.text)

    # store everything we find here
    imagery = {'cities': {}, 'people': {}}

    for kind in ('cities', 'people'):
        for name, url in terms[kind].iteritems():
            dbpedia_live_url = '%s.json' % url.replace('dbpedia.org/resource', 'live.dbpedia.org/data')
            r = requests.get(dbpedia_live_url)
            if r.status_code >= 400:
                continue
            bag = json.loads(r.text)
            for subject, po in bag.iteritems():
                for predicate, o in po.iteritems():
                    if predicate == "http://xmlns.com/foaf/0.1/depiction":
                        for doc in o:
                            print(name, url, doc['value'])
                            imagery[kind][name] = doc['value']

    # save results as single document
    es = elasticsearch.Elasticsearch()
    es.index(index='beek', doc_type='images', id='dbpedia', body=imagery, refresh=True)
