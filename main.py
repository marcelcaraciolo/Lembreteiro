# -*- coding: utf-8 -*-
#!/usr/bin/env python

import random
import re
import urllib
import string
import base64
from datetime import datetime, timedelta

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import mail
from google.appengine.api import urlfetch
from datetime import datetime
from datetime import timedelta

import gdata.gauth
from calendar_api import *
from im import *



HOJE =  0
AMANHA = 1

def GetAuthSubUrl(userkey): 
    next = 'http://www.lembreteiro.appspot.com/chat/lembreteiro/authenticate?userkey=%s' % userkey
    scopes = ['http://www.google.com/calendar/feeds/']
    secure = False  # set secure=True to request a secure AuthSub token
    session = True
    return gdata.gauth.generate_auth_sub_url(next, scopes, secure=secure, session=session)


class UserTalk(db.Model):
    userkey = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now=True)
    username = db.StringProperty()
    token = db.StringProperty()
    ativo = db.BooleanProperty()

def update_attribute(key,attr,value):
    obj = db.get(key)

    if hasattr(obj,attr):
        setattr(obj,attr,value)
        obj.put()

msg_positive = ['sim', 'ok', 'certo', 'positivo', 's', 'ta', 'pode' , 'com certeza', 'yes', 'yeah', 'go', 'aham', 'ahan', 'vai']
msg_negative = ['nao', 'n', 'negativo', 'jamais', 'no', 'nops', 'not', 'never', 'não']


CONFIG_FILE = 'settings.txt'
f = map(string.strip,open(CONFIG_FILE).readlines())
botkey = f[0]
email = f[1]
password = f[2]


class LembreteiroAuth(webapp.RequestHandler):
    def get(self):
        token = self.request.get('token')
        userkey = self.request.get('userkey')
        self.bot = IMService(email,password,  botkey)
        query = UserTalk.gql('WHERE userkey= :Userkey',Userkey=userkey)
        users = query.fetch(1)
        if users:
            for user in users:
                db.run_in_transaction(update_attribute,user.key(),'ativo',True)
                db.run_in_transaction(update_attribute,user.key(),'token',token)
                self.today_activities(userkey)

    def today_activities(self,userkey):
        c_handler = CalendarManager()
        start = datetime.now() + timedelta(hours=4) #timezone from Brasilia
        end =  start + timedelta(days=1)
        end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
        result = c_handler.dateQuery(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
        
        self.bot.speak(userkey,'Sua conta foi sincronizada com sucesso. Voce esta pronto para usar! Use nosso *help* (Digite help) sempre que precisar de auxilio!')
        msg_boas_vindas =  'Voce tem %d atividades pendentes para hoje! Gostaria de lista-las aqui ? (Sim ou Nao)' % len(result.entry)  \
                    if  len(result.entry)  > 0 else 'Voce tem %d atividades pendentes para hoje!'  % len(result.entry) 
        self.bot.speak(userkey,msg_boas_vindas)
        self.response.out.write('<goto=2>')

        
        

class LembreteiroBot(webapp.RequestHandler):
    def get(self):
        self.handle_request()
    
    def post(self):
        self.handle_request()

    def firstTimeWelcome(self,userkey):
        #Usuario nao existe entao vamos cadastrar.
        self.bot.speak(userkey, 'Olá, seja bem vindo ao Lembreteiro: seu Assistente de Lembretes virtual. \
            Percebo que eh a sua primeira vez aqui. Pode me informar seu nome ? (Digite apenas seu *nome*) ')
        self.response.out.write('<goto=2>')
    
    def welcomeMessage(self,username,userkey):
        c_handler = CalendarManager()
        start =  datetime.now() + timedelta(hours=3) #timezone from Brasilia
        end =  start  + timedelta(days=1)  #- timedelta(hours=4)
        end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
        result = c_handler.dateQuery(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))

        self.bot.speak(userkey, 'Ola %s , seja bem vindo ao Lembreteiro: seu Assistente de Lembretes virtual.' % username) 
        msg_boas_vindas =  'Voce tem %d atividades pendentes para hoje! Gostaria de lista-las aqui ? (Sim ou Não)' % len(result.entry) \
                            if  len(result.entry)  > 0 else 'Voce tem %d atividades pendentes para hoje!'  % len(result.entry) 
        self.bot.speak(userkey,msg_boas_vindas)
        if len(result.entry)  > 0:
            self.response.out.write('<goto=2>')
        else:
            self.bot.speak(userkey,'Voce pode usar o help para agendar novos eventos ou acessar sua agenda. Digite help.')
            self.response.out.write('<goto=2>')
     
    
    def handle_request(self):
        step = int(self.request.get('step',default_value=0))
        userkey = self.request.get('userkey')
        msg = self.request.get('msg')
        value1 = self.request.get('value1')
        user = self.request.get('user')
        
        self.bot = IMService('caraciol@gmail.com','mpcara',  "495A77E2-C3D0-4B10-B8BB435CDF5BAA1E")
        
        if userkey:
            query = UserTalk.gql('WHERE userkey= :Userkey',Userkey=userkey)
            users = query.fetch(1)
            if users:
                #Usuario cadastrado.
                if step == 1:
                    for user in users:
                        if not user.ativo:
                            #Usuario nao ativo ainda. Comeca de novo.
                            user.delete()
                            self.firstTimeWelcome(userkey)
                            self.response.out.write('<goto=2>')
                        else:
                            #Boas vindas ao usuario + atividades pendentes de hoje.
                            username = user.username
                            self.welcomeMessage(username,userkey)
                else:
                    #Expandir atividades pendentes (Sim ou Nao)
                    msg = msg.lower()
                    if not users[0].ativo:
                        #Usuario nao ativo ainda. Comeca de novo.
                        user.delete()
                        self.firstTimeWelcome(userkey)
                        self.response.out.write('<goto=2>')
                    elif msg in msg_positive:
                        #mensagem positiva.
                        c_handler = CalendarManager()
                        start = datetime.now() + timedelta(hours=3) #timezone from Brasilia
                        end =  start + timedelta(days=1) #- timedelta(hours=4)
                        end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
                        result = c_handler.DaySchedule(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
                        if result:
                            self.bot.speak(userkey, result)
                    elif msg in msg_negative:
                        #Mensagem Negativa.
                        self.bot.speak(userkey,'Sem problemas! Voce pode usar o help para agendar novos eventos ou acessar sua agenda. Digite help.')
                    elif msg in ['help']:
                        #Mensagem de Help.
                        self.bot.speak(userkey,'Aqui vai o nosso help para mais informacoes: http://lembreteiro.appspot.com/help')
                    elif ':' in msg:
                        #Mensagem por Hora.
                        hour,minute = msg.split(':')
                        c_handler = CalendarManager()
                        start = datetime.now()
                        start = datetime(day=start.day,month=start.month,year=start.year,second=0,minute=int(minute),hour=int(hour)) + timedelta(hours=3)
                        end = datetime(day=start.day,month=start.month,year=start.year,second=59,minute=59,hour=start.hour)
                        result = c_handler.HourSchedule(start, end)
                        if result:
                            self.bot.speak(userkey, result)
                            self.response.out.write('<goto=2>')
                        else:
                            self.bot.speak(userkey,'Nenhuma atividade pendente encontrada para %s  hoje!' % msg)
                            self.response.out.write('<goto=2>')
        
                    elif '/' in msg:
                        #Mensagem por Data.
                        c_handler = CalendarManager()
                        start = datetime.strptime(msg,'%d/%m/%Y') + timedelta(hours=3)
                        end = start + timedelta(days=1)
                        end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
                        result = c_handler.DateSchedule(start, end)
                        if result:
                            self.bot.speak(userkey, result)
                            self.response.out.write('<goto=2>')
                        else:
                            self.bot.speak(userkey,'Nenhuma atividade pendente encontrada para %s !' % msg)
                            self.response.out.write('<goto=2>')
                    elif msg in ['hoje', 'amanha','quarta','quinta']:
                        #Mensagem por Dia da Semana.
                        c_handler = CalendarManager()
                        if msg in ['hoje']:
                            start =  datetime.now() + timedelta(hours=4) #timezone from Brasilia
                            end =  start  + timedelta(days=1) - timedelta(hours=4)
                            end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
                            print start,end
                            result = c_handler.WeekDaySchedule(-2,start,end)
                            if result:
                                self.bot.speak(userkey, result)
                                self.response.out.write('<goto=2>')
                            else:
                                self.bot.speak(userkey,'Nenhuma atividade pendente encontrada para %s !' % msg)
                                self.response.out.write('<goto=2>')
                        elif msg in ['amanha']:
                            start = datetime.now() + timedelta(days=1)  #timezone from Brasilia
                            start = datetime(day=start.day,month=start.month,year=start.year,second=0,minute=0,hour=3)
                            end = start + timedelta(days=1)
                            end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
                            result = c_handler.WeekDaySchedule(-1,start,end)
                            if result:
                                self.bot.speak(userkey, result)
                                self.response.out.write('<goto=2>')
                            else:
                                self.bot.speak(userkey,'Nenhuma atividade pendente encontrada para %s !' % msg)  
                                self.response.out.write('<goto=2>')

                        elif msg in ['quarta', 'quinta']:
                            start = datetime.now().weekday()
                            if msg == 'quarta':
                                week_day = 2
                            elif msg == 'quinta': 
                                week_day = 3  

                            if week_day >= start:
                                days = week_day - start
                            else:
                                days = 7 - start + week_day 
                            start = datetime.now() + timedelta(days=days)  #timezone from Brasilia
                            start = datetime(day=start.day,month=start.month,year=start.year,second=0,minute=0,hour=3)
                            end = start + timedelta(days=1)
                            end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
                            result = c_handler.WeekDaySchedule(msg,start,end)
                            if result:
                                self.bot.speak(userkey, result)
                                self.response.out.write('<goto=2>')
                            else:
                                self.bot.speak(userkey,'Nenhuma atividade pendente encontrada para próximo(a) %s !' % msg)
                                self.response.out.write('<goto=2>')
                    else:
                        #Mensagem Indefinida.
                        self.bot.speak(userkey,'Nao consegui compreender sua mensagem. Voce pode usar o help para agendar novos eventos ou acessar sua agenda. Digite help. ')                    
                        self.response.out.write('<goto=2>')
                    
                    
                    
            else:
                #Sem o usuario cadastrado.
                if step == 1:
                    self.firstTimeWelcome(userkey)
                elif step == 2:
                    #Vamos receber o seu nome.
                    username = msg
                    self.bot.speak(userkey, 'Ola %s , seja bem vindo ao Lembreteiro: seu Assistente de Lembretes virtual.' % username)
                    usr = UserTalk(userkey=userkey,username=username,ativo=False)
                    usr.put()   
                    self.bot.speak(userkey,'Para iniciar a sua agenda, precisamos que voce sincronize sua agenda com Google Calendar. Por favor acesse esta url: %s' % GetAuthSubUrl(userkey))
                    self.response.out.write('<goto=2>')

                    
class UpdateStatusLembreteiro(webapp.RequestHandler):
    def get(self):
        msg = self.request.get('msg')
        if msg:
            url = "https://www.imified.com/api/bot/"

            form_fields = {
                "botkey": "495A77E2-C3D0-4B10-B8BB435CDF5BAA1E",    # Your bot key goes here.
                "apimethod": "updateStatus",  # the API method to call.
                "msg": msg,
                'network' : 'Jabber'
            }

            # Build the Basic Authentication string.  Don't forget the [:-1] at the end!
            base64string = base64.encodestring('%s:%s' % ('caraciol@gmail.com', 'mpcara'))[:-1]
            authString = 'Basic %s' % base64string

            # Build the request post data.
            form_data = urllib.urlencode(form_fields)

            # Make the call to the service using GAE's urlfetch command.
            response = urlfetch.fetch(url=url, payload=form_data, method=urlfetch.POST, headers={'AUTHORIZATION' : authString})

            # Check the response of 200 and process as needed.

            if response.status_code == 200:
                pass
                #####self.response.out.write(msg.decode('utf-8'))
                #self.response.out.write("Worked:Status Code 200.<br>")
                #self.response.out.write(response.content)
            else:
                self.response.out.write("Did not work.<br>")
                self.response.out.write(response.headers)
                self.response.out.write(response.status_code)

def main():
    application = webapp.WSGIApplication([('/chat/lembreteiro/bot', LembreteiroBot),
                                          ('/chat/lembreteiro/update', UpdateStatusLembreteiro),
                                          ('/chat/lembreteiro/authenticate', LembreteiroAuth)

                                         ],
                                       debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
