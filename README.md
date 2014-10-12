Please find the latest code at the [es-backend branch](https://github.com/ahmadassaf/beek.it/tree/es-backend).

----

beek.it - A smart semantic bookmarking system
=======

This project aims at tackling the on-going problem of organizing pages that you access and read on daily basis. We aim at integrating several techniques to autmoactially classify and organize your bookmarks into smart folders.

This project is part of the [HackZurich14](hackzurich.com)

Server
------

To deploy on heroku, set the following config vars:

    $ heroku config
    === beek Config Vars
    ALCHEMY_API_KEY:     2479fc...
    EMBEDLY_API_KEY:     0b64e3...
    ORCHESTRATE_API_KEY: 27b04d...

    $ git push heroku master
