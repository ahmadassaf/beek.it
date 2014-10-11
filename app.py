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
    return pretty_date(dateutil.parser.parse(s))


@app.route('/hello')
def root():
    return app.send_static_file('index.html')


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
        total = es.count(index='beek', body={'query': {'match_all': {}}}).get('count')
        result = es.search(index='beek', body={
            "query" : { "match_all" : {}}, "sort": { "date": { "order": "desc" }}}, size=5)
        return render_template('home.html', docs=result['hits'], total=total)

    es = elasticsearch.Elasticsearch()
    result = es.search(index='beek', doc_type='page', body={
        'query': {'query_string': {'query': '%s' % q}},
        'highlight': {'fields': {'text':
            {"fragment_size" : 90, "number_of_fragments" : 1}}},
        "sort": { "date": { "order": "desc" }}})
    return render_template('home.html', hits=result['hits'])    
    # return "<pre>%s</pre>" % (hits)


@app.route("/api/remove")
def remove_url():
    if request.args.get('id'):
        es = elasticsearch.Elasticsearch()
        es.delete(index='beek', doc_type='page', id=request.args.get('id'))
    return redirect(url_for('home'))


@app.route("/api/add")
def add_url():
    url = request.args.get('url')
    if not url:
        return jsonify(msg='no url supplied'), 400

    q = Queue(connection=Redis())
    # First, index the page
    index_job = q.enqueue(index, url)
    # In parallel, do Alchemy on URL and store it in a separate doc type
    alchemy_job = q.enqueue(query_alchemy, url, depends_on=index_job)
    # Embedly ...
    embedly_job = q.enqueue(query_embedly, url, depends_on=alchemy_job)
    # Count the words in the page ...
    wordcount_job = q.enqueue(count_words, url_to_doc_id(url), depends_on=embedly_job)

    # return jsonify(msg="ok enqueued")
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
