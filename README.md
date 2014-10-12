beek.it
=======

A smarter semantic bookmarking system

This project aims at tackling the on-going problem of organizing pages that you access and
read on daily basis. We aim at integrating several techniques to automatically classify
and organize your bookmarks into smart folders.

This project is part of the [HackZurich14](http://hackzurich.com)

* https://www.hackerleague.org/hackathons/hackzurich-2014/hacks/beek-dot-it
* https://www.youtube.com/watch?v=TuB6y8oQPmI

beek server
-----------

An elasticsearch server serves as a backend with an API/webapp wrapper around it,
that exposes various information.

Check if a page is already bookmarked (return true or false):

    $ curl http://localhost:5000/bookmarked?url=http://www.heise.de
    {
        "bookmarked": true
    }

List all terms (categories, cities, people) of all saved bookmarks:

    $ curl http://localhost:5000/terms
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

List imagery from wikipedia, which is made available via dbpedia, shared
into cities and people:

    $ curl http://localhost:5000/images
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

Add a new bookmark:

    $ curl http://localhost:5000/api/add?url=http://www.bbc.com/autos/story/20141008-is-this-the-best-porsche-911

Remove a bookmark via ID, which is the SHA1 of the URL:

    $ curl http://localhost:5000/api/remove?id=00118581fcb1fa384d30b76a7fa2a6a72025e859

----

Home (`/`) and `api/search` are user facing interfaces.

