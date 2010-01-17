#!/usr/bin/env python
#
# This code is derived from work by Ryan Lee Schneider
# which was the @annyong_bluth twitter search
#
import twitter
import re
from datetime import datetime, timedelta
from model import EpicTweet, LastSearch
import urllib
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

directed_annyongs_regex = re.compile(r'(\@[\w_]+ *)+( \:)? #haiti')

USERNAME = 'haiti_tweaked'
PASSWORD = '<redacted>'
USER_AGENT = 'Unique UserAgent Here'

def Search(searchquery):
    api = twitter.Api(cache=None)
    api.SetCredentials(USERNAME, PASSWORD)
    api.SetUserAgent(USER_AGENT)
    annyongs = []
    
    query = LastSearch.all()
    results = query.fetch(1)
    if results:
        lastsearch = results[0]
    else:
        lastsearch = LastSearch()

    # urllib.quote('#haiti')
    data = api.Search(searchquery, perpage=100)
            # , since_id=lastsearch.id
    if data:
        statuses = [twitter.Status.NewFromJsonDict(x) for x in data['results']]
        lastsearch.id = data['max_id']
    else:
        statuses = []
    
    hits = len(statuses)
    if hits:
        YFD('searched', len(statuses), 'hits', api=api)
    accepted = 0
    rejected = 0
    
    for s in statuses:
        annyong = EpicTweet()
        annyong.replied = False
        annyong.original_text = s.text
        annyong.tweet_id = s.id
        annyong.sender = s.user.name
        annyong.sender_id = s.user.id
        annyong.date = datetime.utcfromtimestamp(s.created_at_in_seconds)
        text = s.text
             #       .lower()
        length = len(text)
        accepted += 1
        annyong.accepted = True
        annyongs.append(annyong)
        lastsearch.id = max(lastsearch.id, s.id)
        YFD('accepted', accepted, 'annyongs', api=api)
    return (lastsearch, annyongs)        
        
def YFD(action, amount=1, units=None, api=None):
    return #disable for now
#    if not api:
#        api = twitter.Api(cache=None)
#        api.SetCredentials('haiti_tweaked', 'katecom30')
#    post = 'd yfd %s %d' % (action, amount)
#    if units:
#        post += ' %s' % (units)
#    api.PostUpdate(status=post)

class SearchPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        (lastsearch, annyongs) = Search('%23haiti+%23need+OR+%23ruok+OR+%23imok+OR+%23offering')
        lastsearch.put()
        keys = [a.put() for a in annyongs]
        results = """
<search>
%s
<EpicTweets count='%d'>%s
</EpicTweets>
</search>
""" % (lastsearch, len(annyongs), u''.join([unicode(a) for a in annyongs]))
        self.response.out.write(results)

class LocationsPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        (lastsearch, annyongs) = Search('%23haiti+%23loc')
        lastsearch.put()
        keys = [a.put() for a in annyongs]
        results = """
<html>
<body>
These %d tweets have locations:<br/>
<small><i>Times are EST (GMT-6)</i></small>
<ul>%s
</ul>
</body></html>
""" % (len(annyongs), u''.join([a.toHtml() for a in annyongs]))
        self.response.out.write(results)

class NeedsPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        (lastsearch, annyongs) = Search('%23haiti+%23need')
        lastsearch.put()
        keys = [a.put() for a in annyongs]
        results = """
<html>
<body>
These %d tweets listed needs:<br/>
<small><i>Times are EST (GMT-6)</i></small>
<ul>%s
</ul>
</body></html>
""" % (len(annyongs), u''.join([a.toHtml() for a in annyongs]))
        self.response.out.write(results)

class AreYouOkPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        (lastsearch, annyongs) = Search('%23haiti+%23ruok')
        lastsearch.put()
        keys = [a.put() for a in annyongs]
        results = """
<html>
<body>
These %d tweets asked R U OK?<br/>
<small><i>Times are EST (GMT-6)</i></small>
<ul>%s
</ul>
</body></html>
""" % (len(annyongs), u''.join([a.toHtml() for a in annyongs]))
        self.response.out.write(results)

class ImOkPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        (lastsearch, annyongs) = Search('%23haiti+%23imok')
        lastsearch.put()
        keys = [a.put() for a in annyongs]
        results = """
<html>
<body>
These %d tweets are from people saying IMOK:<br/>
<small><i>Times are EST (GMT-6)</i></small>
<ul>%s
</ul>
</body></html>
""" % (len(annyongs), u''.join([a.toHtml() for a in annyongs]))
        self.response.out.write(results)
        
        
class AnnyongPage(webapp.RequestHandler):
    def render(self, annyongs):
        self.response.headers['Content-Type'] = 'text/plain'
        arr = [a for a in annyongs]
        results = """
<Annyongs count='%d'>%s
</Annyongs>""" % (len(arr), u''.join([unicode(a) for a in arr]))
        self.response.out.write(results)

class ReplyPage(AnnyongPage):
    def reply(self, annyong):
        try:
            if annyong.age() > timedelta(hours=3):
                annyong.accepted = False
                annyong.reject_reason = 'Too old to reply: %s' % (annyong.age())
                annyong.put()
                return (False, annyong, '')
            api = twitter.Api(cache=None)
            api.SetCredentials('users@gmail.com', 'mygmailpw')
            post = '@%s Annyong.' % (annyong.sender)
            annyong.replied = True
            api.PostUpdate(status=post, in_reply_to_status_id=annyong.tweet_id)
        except:
            import traceback
            annyong.reject_reason = 'Exception: %s' % (traceback.format_exc())
            annyong.put()
            return (annyong.replied, annyong, post)
        annyong.put()
        return (True, annyong, post)

    def get(self):
        keepLooking = True
        results = []
        while keepLooking:
            need_replies = db.GqlQuery("""
                SELECT * from Annyong WHERE accepted = :accepted AND replied = :replied
                ORDER BY tweet_id ASC LIMIT 1""", accepted=True, replied=False)
            if need_replies:
                replies = [self.reply(r) for r in need_replies]
                if not len(replies):
                    keepLooking = False
                for r in replies:
                    if r[0] == True:
                        keepLooking = False
                results.extend(replies)
            else:
                results.append((False, None, ''))
                keepLooking = False
        self.response.headers['Content-Type'] = 'text/plain'
        response = '<replies>'
        for (result, annyong, post) in results:
            response += "\n  <reply result='%s'>" % (result)
            response += str(annyong)
            response += "\n      <post>%s</post></reply>" % (post)
        response += '</replies>'
        count = len(replies)
        if count:
            YFD('posted', count, 'annyongs')
        self.response.out.write(response)
        
        
application = webapp.WSGIApplication(
                                     [('/search', SearchPage),
                                      ('/locations', LocationsPage),
                                      ('/need', NeedsPage),
                                      ('/imok', ImOkPage),
                                      ('/ruok', AreYouOkPage),
                                      ('/reply', ReplyPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()