#!/usr/bin/python
#-*- coding: utf-8 -*-
#2012 Ole Trenner


import collections
import json
import traceback
import urllib
import urllib2
from xml.sax.saxutils import escape

import web


class DribbbleApi(object):
    """Dribbble API client.

    >>> d = DribbbleApi(printrequests=True)
    >>> d.players_shots_following('someplayer')
    'http://api.dribbble.com/players/someplayer/shots/following'

    >>> d.players_shots_following('someplayer', page=3)
    'http://api.dribbble.com/players/someplayer/shots/following?page=3'
    """

    DRIBBBLE = "http://api.dribbble.com/"
    FOLLOWING = "players/%(user)s/shots/following"

    def __init__(self, printrequests=False):
        self._debug = printrequests

    def players_shots_following(self, player, **kwargs):
        return self._request(self.FOLLOWING % dict(user=player), **kwargs)

    def _request(self, path, **kwargs):
        url = '%s%s?%s' % (self.DRIBBBLE, path, urllib.urlencode(kwargs))
        url = url.strip('?')
        if self._debug:
            return url
        try:
            response = urllib2.urlopen(url)
            return json.load(response)
        except Exception, e:
            raise Exception('Couldn\'t access "%s", error "%s"' % (url, e))


class DribbbleFeed(object):
    """Dribbble feed generator.

    >>> d = DribbbleFeed()
    >>> d.players_shots_following(dict(shots=[])) #doctest:+ELLIPSIS
    '<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0">...</rss>'
    """

    SKELETON = '<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0"><channel>'\
               '<title>%(title)s</title><description>%(description)s</description>'\
               '<link>%(link)s</link><lastBuildDate>%(builddate)s</lastBuildDate>'\
               '<pubDate>%(pubdate)s</pubDate><ttl>%(ttl)s</ttl>%(items)s</channel></rss>'
    ITEM     = '<item><title>%(title)s</title><description>%(content)s</description>'\
               '<link>%(link)s</link><guid>%(guid)s</guid><pubDate>%(pubdate)s</pubDate></item>'
    CONTENT  = '<a href="%(url)s"><img alt="" src="%(image_url)s"> %(title)s</a>'

    def players_shots_following(self, data):
        def itemize(data):
            return self.ITEM % dict(
                title=data['title'],
                content=escape(self.CONTENT % data),
                link=data['url'],
                guid=data['url'],
                pubdate=data['created_at']
            )
        items = ''.join((itemize(i) for i in data['shots']))
        return self._feed(title='Shots', items=items, ttl=21600)

    def _feed(self, **data):
        data = collections.defaultdict(str, data)
        return self.SKELETON % data


class DribbbleFeeder(object):
    """Dribbble feed request handler.
    """
    def GET(self, username):
        username = username or '_'
        try:
            d = DribbbleApi()
            f = DribbbleFeed()
            data = d.players_shots_following(username)
            rss = f.players_shots_following(data)
            return rss
        except Exception, e:
            return e



urls = ('/(.+)', 'DribbbleFeeder')
application = web.application(urls, globals())


if __name__ == '__main__':
    wsgiapp = application.wsgifunc()
    web.wsgi.runwsgi(wsgiapp)

