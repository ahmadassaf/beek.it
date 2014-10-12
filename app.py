# coding: utf-8

"""
A microservice, that takes an URL and saves the url in some database.
"""

from flask import Flask, request, abort, jsonify, g, render_template, redirect, url_for
from jobs import *
from redis import Redis
from rq import Queue
from utils import url_to_doc_id, pretty_date
import datetime
import dateutil.parser
import elasticsearch
import time
import our_evernote

app = Flask(__name__)

@app.template_filter('human_category')
def human_category(s):
    """ 2014-10-11T08:53:18.392370 """
    cats = {
        'culture_politics': 'Culture/Politics',
        'recreation': 'Recreation',
        'computer_internet': 'Computer/Internet',
        'science_technology': 'Science/Technology',
        'arts_entertainment': 'Arts/Entertainment',
        'business': 'Business',
    }
    return cats.get(s, s)

@app.template_filter('human_time')
def human_time(s):
    """ 2014-10-11T08:53:18.392370 """
    try:
        return pretty_date(dateutil.parser.parse(s))
    except Exception as err:
        print(err)
    return s

@app.route('/hello')
def root():
    return app.send_static_file('index.html')

@app.route("/bookmarked")
def bookmarked():
    import urllib
    url = request.args.get('url')
    query = {'query_string': {'query': 'url:"%s"' % url}}
    es = elasticsearch.Elasticsearch()
    result = es.search(index='beek', body={
            "query" : query}, size=100)
    return jsonify({'bookmarked': result['hits']['total']!=0})

<<<<<<< HEAD
@app.route("/terms")
def terms():
=======
def filter_keywords(keywords):
    return [ keyword for keyword in keywords if keyword > str(0.95)]

def get_terms():
>>>>>>> 77e0288a225a154709ef409ba8590d0b5a6e560b
    es = elasticsearch.Elasticsearch()
    result = es.search(index='beek', body={
            "query" : { "match_all" : {}}}, size=100)
    data = result['hits']['hits']
    cities = filter_type_from_results('City', data)
    people = filter_type_from_results('Person', data)

    keywords = set()
    cats = set()
    for row in data:
        cat = row['_source'].get('category', None)
        if cat:
            cats.add(cat)
        for key in row['_source'].get('keywords', []):
            keywords.add(key['text'])

    keywords = filter_keywords(keywords)

    return cities, people, list(cats), keywords

@app.route("/terms")
def terms():
    cities, people, cats, keywords = get_terms()
    return jsonify({'cities':cities, 'people':people, 'categories':cats, 'keywords':keywords})

@app.route("/images")
def images():
    es = elasticsearch.Elasticsearch()
    try:
        result = es.get_source(index='beek', doc_type='images', id='dbpedia')
    except Exception as err:
        return jsonify(msg=str(err))
    return jsonify(**result)

@app.route("/groups")
def groups():
    es = elasticsearch.Elasticsearch()
    try:
        result = es.get_source(index='beek', doc_type='groups', id='dbpedia')
    except Exception as err:
        return jsonify(msg=str(err))
    return jsonify(**result)

def filter_type_from_results(ent_type, results):
    terms = dict()
    for result in results:
        print result['_source'].keys()
        for entity in result['_source'].get('entities',[]):

            if entity['type'] == ent_type and entity.get('disambiguated'):
                    disam = entity['disambiguated']
                    terms[ disam['name'] ] = disam.get('dbpedia', '')
    return terms


@app.route("/related")
def related():
    url = request.args.get('url')
    if not url:
        return jsonify(msg='url parameter required')

    es = elasticsearch.Elasticsearch()
    result = es.search(index='beek', doc_type='page', body={'query':
               {'query_string': {'query': 'url:"%s"' % url}}})
    hits = result['hits']['hits']
    return jsonify(related=hits)


@app.route("/")
def home():
    q = request.args.get('q')
    # add new URL
    if q and q.strip().startswith('+'):
        url = q.strip().strip('+ ')
        # append http:// if needed
        if not url.startswith('http'):
            url = 'http://%s' % url
        return redirect(url_for('add_url', url=url))
    if not q:
        # get some stats
        es = elasticsearch.Elasticsearch()
        total = es.count(index='beek', doc_type='page', body={'query': {'match_all': {}}}).get('count')
        result = es.search(index='beek', body={
            "query" : { "match_all" : {}}}, size=5)

        cities, people, cats, _ = get_terms()
        images = es.get_source(index='beek', doc_type='images', id='dbpedia')
        return render_template('home.html', docs=result['hits'], total=total,
                       cities=cities, people=people, cats=cats,
                       images=images)

    es = elasticsearch.Elasticsearch()
    query = {'query_string': {'query': '%s' % q}}
    result = es.search(index='beek', doc_type='page', body={
        'query': query,
        'highlight': {'fields': {'text':
            {"fragment_size" : 250, "number_of_fragments" : 3}}}})

    people = filter_type_from_results('Person', result['hits']['hits'])

    return render_template('home.html', hits=result['hits'], people=people)
    # return "<pre>%s</pre>" % (hits)

@app.route("/query")
def query():
    q = request.args.get('q')

    es = elasticsearch.Elasticsearch()
    query = {'query_string': {'query': '%s' % q}}
    result = es.search(index='beek', doc_type='page', body={
        'query': query,
        'highlight': {'fields': {'text':
            {"fragment_size" : 90, "number_of_fragments" : 1}}}})['hits']['hits']

    output = []

    for row_raw in result:
        row = row_raw['_source']
        import re
        m = re.search('<title>(.*)</title>', row['content'])
        if not m:
            continue
        title = m.group(1)

        images = {}
        try:
            images = es.get_source(index='beek', doc_type='images', id='dbpedia')
        except Exception as err:
            print 'IMAGES NOT DOWNLOADED'

        cities = []
        people = []
        for entity in row.get('entities',[]):
            if entity['type'] == 'City' and entity.get('disambiguated') and entity.get('disambiguated').get('geo'):
                city_desc = entity.get('disambiguated')
                lat_long = city_desc['geo'].split(' ')
                city_desc['latitude'] = lat_long[0]
                city_desc['longitude'] = lat_long[1]
                city_desc.pop('geo')
                city_desc['image'] = images['cities'].get(city_desc['name'],'')
                cities.append(city_desc)
            elif entity['type'] == 'Person' and entity.get('disambiguated'):
                person_desc = entity.get('disambiguated')
                person_desc['image'] = images['people'].get(person_desc['name'],'')
                person = entity.get('disambiguated')
                people.append(person)

        output.append(
            {
            'url': row['url'],
            'date': row['date'],
            'id': row_raw['_id'],
            'title': title,
            'excerpt': row_raw['highlight']['text'] if row_raw.get('highlight') else '',
            'type' : row['embedly']['data']['type'] if row.get('embedly') else 'link',
            'thumbnail': row['embedly']['data']['thumbnail_url'] if row.get('embedly') else '',
            'cities': cities,
            'people': people
            }
        )
    return jsonify({'out':output})

@app.route("/api/remove")
def remove_url():
    if request.args.get('id'):
        es = elasticsearch.Elasticsearch()
        es.delete(index='beek', doc_type='page', id=request.args.get('id'))
    return redirect(url_for('home'))

@app.route("/api/remove_url")
def remove_url_by_url():
    if request.args.get('url'):
        es = elasticsearch.Elasticsearch()
        try:
            es.delete(index='beek', doc_type='page', id=url_to_doc_id(request.args.get('url')))
        except Exception as err:
            print(err)
            pass
    return redirect(url_for('home'))

@app.route("/api/add")
def add_url():
    url = request.args.get('url')
    if not url:
        return jsonify(msg='no url supplied'), 400

    es = elasticsearch.Elasticsearch()
    try:
        result = es.get(index='beek', doc_type='page', id=url_to_doc_id(request.args.get('url')))
        return redirect(url_for('home'))
    except Exception as err:
        pass

    q = Queue(connection=Redis())
    # First, index the page
    index_job = q.enqueue(index, url)
    # In parallel, do Alchemy on URL and store it in a separate doc type
    alchemy_job = q.enqueue(query_alchemy, url, depends_on=index_job)
    # Embedly ...
    embedly_job = q.enqueue(query_embedly, url, depends_on=alchemy_job)
    # Count the words in the page ...
    wordcount_job = q.enqueue(count_words, url_to_doc_id(url), depends_on=embedly_job)
    # Terms images service
    termimages_job = q.enqueue(get_terms_images, depends_on=wordcount_job)
    # Calculate some readability measures
    readability_job = q.enqueue(calculate_readability_measures, url_to_doc_id(url), depends_on=termimages_job)
    # group people
    group_people_job = q.enqueue(group_people, depends_on=readability_job)

    # return jsonify(msg="ok enqueued")
    return redirect(url_for('home'))

@app.route("/api/search")
def search():
    parts = []
    fulltext = request.args.get('fulltext')
    if fulltext:
        parts.append('_source.text:%s' % fulltext)

    city = request.args.get('city')
    if city:
        parts.append('(entities.type:City AND entities.text:"%s")' % city)

    country = request.args.get('country')
    if country:
        parts.append('(entities.type:Country AND entities.text:"%s")' % country)

    continent = request.args.get('continent')
    if continent:
        parts.append('(entities.type:Continent AND entities.text:"%s")' % continent)

    region = request.args.get('region')
    if region:
        parts.append('(entities.type:Country AND entities.text:"%s")' % country)

    continent = request.args.get('continent')
    if continent:
        parts.append('(entities.type:Continent AND entities.text:"%s")' % continent)

    es = elasticsearch.Elasticsearch()
    result = es.search(index='beek', doc_type='page', body={
        'query': {'query_string': {'query': '%s' % " AND ".join(parts)}},
        'highlight': {'fields': {'text': {"fragment_size" : 300, "number_of_fragments" : 1}}}})
    return render_template('home.html', hits=result['hits'])

@app.route("/api/load_from_evernote")
def load_from_evernote():
    token = request.args.get('token')
    token = 'S=s1:U=8fa64:E=1505674a78d:C=148fec37b28:P=1cd:A=en-devtoken:V=2:H=557207e871d827a672dd55ffdb6b0a11'
    q = Queue(connection=Redis())
    # First, index the page
    index_job = q.enqueue(process_evernote, '__token__')

    return jsonify({'ok': True})



if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        app.run(host='0.0.0.0', port=int(sys.argv[1]), debug=True)
    else:
        app.run(host='0.0.0.0', debug=True)
