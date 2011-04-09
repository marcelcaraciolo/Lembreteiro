
import urllib
import base64
from google.appengine.api import urlfetch


class IMService(object):

    
    def __init__(self,username,password,botkey):
        self.url = "https://www.imified.com/api/bot/"
        self.username = username
        self.password = password
        self.botkey = botkey
    
    def speak(self,userkey,message):

        form_fields = {
            "botkey": self.botkey,    # Your bot key goes here.
            "apimethod": "send",  # the API method to call.
            "userkey": str(userkey),  # User Key to lookup with getuser.
            "msg": message,
            'network' : 'Jabber'
        }

        # Build the Basic Authentication string.  Don't forget the [:-1] at the end!
        base64string = base64.encodestring('%s:%s' % (self.username, self.password))[:-1]
        authString = 'Basic %s' % base64string

        # Build the request post data.
        form_data = urllib.urlencode(form_fields)

        # Make the call to the service using GAE's urlfetch command.
        response = urlfetch.fetch(url=self.url, payload=form_data, method=urlfetch.POST, headers={'AUTHORIZATION' : authString})

        # Check the response of 200 and process as needed.

        if response.status_code == 200:
            return True
        else:
            return False