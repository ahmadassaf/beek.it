# beek.it

> A smarter semantic bookmarking system

This project aims at tackling the on-going problem of organizing pages that you access and read on daily basis. We aim at integrating several techniques to automatically classify and organize your bookmarks into smart folders.

This project is part of the [HackZurich14](http://hackzurich.com) | [Watch video](https://www.youtube.com/watch?v=TuB6y8oQPmI)

## Setting up

The beek.it consists of An elasticsearch server serves as a backend with an API/webapp wrapper around it, that exposes various information. General requirements are:

 - [ElasticSearch (v5.x)](https://www.elastic.co/products/elasticsearch): a distributed, RESTful search and analytics engine capable of solving a growing number of use cases
 - [redis v3.x](https://redis.io): in-memory data structure store, used as a database, cache and message broker
 - [rqworker](http://python-rq.org): a simple Python library for queueing jobs and processing them in the background with workers

### Starting up:

 1. Make sure that all python dependencies are install with `pip install -r requirements.txt`
 2. Starting up the server requires that an ElasticSearch and redis instance are running, then an `rqworker` worker is running as well using the `rqworker` command

### Server Methods

#### Check if a page is already bookmarked (return true or false):

```bash
$ curl http://localhost:5000/bookmarked?url=http://www.heise.de
```
```javascript
{
    "bookmarked": true
}
```

#### List all terms (categories, cities, people) of all saved bookmarks:

```bash
$ curl http://localhost:5000/terms
```
```javascript
{
  "categories": [
    "recreation",
    "business",
    "computer_internet",
    "culture_politics",
    "arts_entertainment"
  ],
  "cities": {
    "Amphipolis": "http://dbpedia.org/resource/Amphipolis",
    "Anbar (town)": "http://dbpedia.org/resource/Anbar_(town)",
    ...
  },
  "people": {
    "Adam Ashley-Cooper": "http://dbpedia.org/resource/Adam_Ashley-Cooper",
    ...
  }
}
```

#### List imagery from wikipedia, which is made available via dbpedia, shared into cities and people:

```bash
$ curl http://localhost:5000/images
```
```javascript

{
  "cities": {
    "Amphipolis": "http://commons.wikimedia.org/wiki/Special:FilePath/2011_Dimos_Amfipolis.png",
    ...
  },
  "people": {
    "Barack Obama": "http://commons.wikimedia.org/wiki/Special:FilePath/President_Barack_Obama.jpg",
    ...
  },
}
```


#### Add a new bookmark:

```bash
$ curl http://localhost:5000/api/add?url=http://www.bbc.com/autos/story/20141008-is-this-the-best-porsche-911
```

#### Remove a bookmark via ID, which is the SHA1 of the URL:

```bash
$ curl http://localhost:5000/api/remove?id=00118581fcb1fa384d30b76a7fa2a6a72025e859
```

> Home (`/`) and `api/search` are user facing interfaces.

