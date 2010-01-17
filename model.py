
from google.appengine.ext import db
from datetime import datetime,timedelta

class LastSearch(db.Model):
    id = db.IntegerProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    
    def __repr__(self):
        return "<lastsearch id='%s' date='%s' />" % (self.id, self.date)
    
    
class EpicTweet(db.Model):
    tweet_id = db.IntegerProperty()
    sender = db.StringProperty()
    sender_id = db.IntegerProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    original_text = db.StringProperty(multiline=True)
    accepted = db.BooleanProperty()
    replied = db.BooleanProperty()
    reject_reason = db.StringProperty(multiline=True)
    
    def toHtml(self):
        return """
<li>
On %s %s said: <br/>
<pre>%s</pre>
</li>""" % (self.date-timedelta(hours=6), self.sender,
 self.original_text)

    def __repr__(self):
        return """
<EpicTweet id='%d' accepted='%s' replied='%s'>
    <date>%s</date>
    <age>%s</age>
    <sender name='%s' id='%d'/>
    <text>%s</text>
</EpicTweet>""" % (self.tweet_id, self.accepted, self.replied, 
                 self.date, self.age(), self.sender, self.sender_id,
                 self.original_text)

    def age(self):
        return datetime.utcnow() - self.date
