# -*- coding: utf-8 -*-
#!/usr/bin/env python

import random
import re
import urllib
import base64
from datetime import datetime, timedelta

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import mail

class UserTalk(db.Model):
	userkey = db.StringProperty()
	timestamp = db.DateTimeProperty(auto_now=True)
	ativo = db.BooleanProperty()




class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')


def main():
	application = webapp.WSGIApplication([('/chat/lembreteiro/bot', LembreteiroBot)
										 ],
                                       debug=True)
	util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
