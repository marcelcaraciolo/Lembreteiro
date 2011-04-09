# -*- coding: utf-8 -*-

import unittest
import string
from datetime import datetime,timedelta

from google.appengine.ext import testbed
from google.appengine.ext import db

from im import *
from main import UserTalk, GetAuthSubUrl
from calendar_api import *


msg_positive = ['sim', 'ok', 'certo', 'positivo', 's', 'ta', 'pode' , 'com certeza', 'yes', 'yeah', 'go', 'aham', 'ahan', 'vai']
msg_negative = ['nao', 'n', 'negativo', 'jamais', 'no', 'nops', 'not', 'never']


def update_attribute(key,attr,value):
    obj = db.get(key)

    if hasattr(obj,attr):
        setattr(obj,attr,value)
        obj.put()


CONFIG_FILE = 'tests/config.txt'

class IMTestCase(unittest.TestCase):
    
    def setUp(self):
        f = map(string.strip,open(CONFIG_FILE).readlines())
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        self.unitkey = f[0]
        self.userkey = f[1]
        self.email = f[2]
        self.password = f[3]
        
        self.bot = IMService(self.email,self.password,self.unitkey)
        
    
    def testSendMessage(self):  
        self.assertEquals(True,self.bot.speak(self.userkey,'Isto é um teste'))
        
    def tearDown(self):
        self.testbed.deactivate()

class MainLogicTestCase(unittest.TestCase):

    def setUp(self):
        f = map(string.strip,open(CONFIG_FILE).readlines())
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.unitkey = f[0]
        self.userkey = f[1]
        self.email = f[2]
        self.password = f[3]

        self.bot = IMService(self.email,self.password,self.unitkey)


    def testWelcomeFirstTime(self):
        step = 1
        userkey = self.userkey
        msg = 'Olá'
        value1 = ''
        user = ''

        #Caso 1: Usuario Chegando pela primeira vez no Lembreteiro.
        if userkey:
            query = UserTalk.gql('WHERE userkey= :Userkey',Userkey=userkey)
            users = query.fetch(1)
            if users:
                if step == 1:
                    self.assertTrue(users == None)
            else:
                #Sem o usuario cadastrado.
                if step == 1:
                    #Usuario nao existe entao vamos cadastrar.
                    r = self.bot.speak(userkey, 'Ola, seja bem vindo ao Lembreteiro: seu Assistente de Lembretes virtual. \
                        Percebo que eh a sua primeira vez aqui. Pode me informar seu nome ? (Digite apenas seu *nome*) ')
                    step = 2     #self.response.out.write('<goto=2>')
                    self.assertEquals(r,True)
                    self.assertEquals(len(UserTalk.gql('WHERE userkey= :Userkey',Userkey=userkey).fetch(1)),0)

    def testWelcomeAuthentication(self):
        step = 2
        userkey = self.userkey
        msg = 'Marcel'
        value1 = ''
        user = ''

        #Caso 1: Usuario Chegando pela primeira vez no Lembreteiro.
        if userkey:
            query = UserTalk.gql('WHERE userkey= :Userkey',Userkey=userkey)
            users = query.fetch(1)
            if users:
                if step == 1:
                    self.assertTrue(users == None)
            else:
                #Sem o usuario cadastrado.
                if step == 1:
                    #Usuario nao existe entao vamos cadastrar.
                    r = self.bot.speak(userkey, 'Ola, seja bem vindo ao Lembreteiro: seu Assistente de Lembretes virtual. \
                        Percebo que eh a sua primeira vez aqui. Pode me informar seu nome ? (Digite apenas seu *nome*) ')
                    step = 2     #self.response.out.write('<goto=2>')
                    self.assertEquals(r,True)
                    self.assertEquals(len(UserTalk.gql('WHERE userkey= :Userkey',Userkey=userkey).fetch(1)),0)
                elif step == 2:
                    #Vamos receber o seu nome.
                    username = msg
                    r = self.bot.speak(userkey, 'Ola %s , seja bem vindo ao Lembreteiro: seu Assistente de Lembretes virtual.' % username)
                    self.assertEquals(r,True)
                    usr = UserTalk(userkey=userkey,username=username,ativo=False)
                    usr.put()   
                    r = self.bot.speak(userkey,'Para iniciar a sua agenda, precisamos que voce sincronize sua agenda com Google Calendar. Por favor acesse esta url: %s' % GetAuthSubUrl(userkey))
                    self.assertEquals(r,True)                   
                    step = 3 #self.response.out.write('<goto=3>')



    def test_authentication_sucess(self):
        token = 'teste'
        userkey  = self.userkey

        usr = UserTalk(userkey=userkey,username= 'marcel',ativo=False)
        usr.put()

        query = UserTalk.gql('WHERE userkey= :Userkey',Userkey=userkey)
        users = query.fetch(1)
        if users:             
            for user in users:
                db.run_in_transaction(update_attribute,user.key(),'ativo',True)
                db.run_in_transaction(update_attribute,user.key(),'token',token)
                #self.bot.speak(userkey,'Sua conta foi sincronizada com sucesso. Voce esta pronto para usar! Use nosso *help* (Digite help) sempre que precisar de auxilio!')

        query = UserTalk.gql('WHERE userkey= :Userkey',Userkey=userkey)
        users = query.fetch(1)

        self.assertEquals(users[0].ativo,True)
        self.assertEquals(users[0].username,'marcel')
        self.assertEquals(users[0].token,'teste')

        c_handler = CalendarManager()
        start = datetime.now() + timedelta(hours=4) #timezone from Brasilia
        end =  start + timedelta(days=1)
        end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
        result = c_handler.dateQuery(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
        msg_boas_vindas =  'Voce tem %d atividades pendentes para hoje! Gostaria de lista-las aqui ? (Sim ou Nao)' % len(result.entry)  if  len(result.entry)  > 0 else 'Voce tem %d atividades pendentes para hoje!'  % len(result.entry) 
        r = self.bot.speak(userkey,msg_boas_vindas)
        self.assertEquals(r,True)
        if len(result.entry) > 0:
            step = 3 #self.response.out.write('<goto=2>')
        else:
            step = 4 #self.response.out.write('<goto=4>')


    def test_today_activities(self):
        msgs = ['SIM', 'NAO', 'anh']
        step = 3
        userkey  = self.userkey
        if step == 3:
            for i,msg in enumerate(msgs):
                msg = msg.lower()
                if msg in msg_positive:
                    c_handler = CalendarManager()
                    start =  datetime(2011,04,9,19,34,34) #datetime.now() + timedelta(hours=4) #timezone from Brasilia
                    end =  start + timedelta(days=1)
                    end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
                    result = c_handler.DaySchedule(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
                    if result:
                        self.bot.speak(userkey, result)
                        x = 1
                elif msg in msg_negative:
                    #self.bot.speak(userkey,'Sem problemas! Voce pode usar o help para agendar novos eventos ou acessar sua agenda. Digite help.')
                    x = 0
                else:
                    #self.bot.speak(userkey,'Nao consegui compreender sua mensagem. Voce pode usar o help para agendar novos eventos ou acessar sua agenda. Digite help. ')
                    x = -1
                step = 4#self.response.out.write('<goto=4>')

                if i == 0:
                    self.assertEquals(x,1)
                elif i == 1:
                    self.assertEquals(x,0)
                elif i == -1:
                    self.assertEquals(x,-1)


    def test_date_activities(self):
        msg = '10/04/2011'
        step = 5
        userkey  = self.userkey

        msg = msg.lower()

        if step == 5:
            c_handler = CalendarManager()
            start = datetime.strptime(msg,'%d/%m/%Y') + timedelta(hours=3)
            end = start + timedelta(days=1)
            end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
            result = c_handler.DateSchedule(start, end)
            if result:
                self.bot.speak(userkey, result)
                step = 4 #self.response.out.write('<goto=4>')
            else:
                self.bot.speak(userkey,'Nenhuma atividade pendente encontrada para %s !' % msg)
                step = 4 #self.response.out.write('<goto=4>')




    def test_hour_activities(self):
        msgs = ['18:00','18:45', '10:00', '23:00']
        step = 6
        userkey  = self.userkey

        if step == 6:

            for i,msg in enumerate(msgs):

                msg = msg.lower() #Extrair hora usando regex.
                hour,minute = msg.split(':')
                c_handler = CalendarManager()
                start = datetime(2011,04,9,0,0,0)#datetime.now()
                start = datetime(day=start.day,month=start.month,year=start.year,second=0,minute=int(minute),hour=int(hour)) + timedelta(hours=3)
                end = datetime(day=start.day,month=start.month,year=start.year,second=59,minute=59,hour=start.hour)
                result = c_handler.HourSchedule(start, end)
                if result:
                    self.bot.speak(userkey, result)
                    step = 4 #self.response.out.write('<goto=4>')
                else:
                    self.bot.speak(userkey,'Nenhuma atividade pendente encontrada para %s  hoje!' % msg)
                    step = 4 #self.response.out.write('<goto=4>')

                if i == 0:
                    result = c_handler.dateQuery(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
                    self.assertEquals(len(result.entry),1)
                elif i == 1:
                    result = c_handler.dateQuery(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
                    self.assertEquals(len(result.entry),1)                    
                elif i == 2:
                    result = c_handler.dateQuery(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
                    self.assertEquals(len(result.entry),0)                
                elif i == 3:
                    result = c_handler.dateQuery(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
                    self.assertEquals(len(result.entry),2)



    def test_week_day_activities(self):
        msgs = ['hoje', 'amanha']
        step = 7
        userkey  = self.userkey

        if step == 7:       
            for i,msg in enumerate(msgs):               
                msg = msg.lower() #Extrair data da semana usando regex.
                c_handler = CalendarManager()
                if msg in ['hoje']:
                    start =  datetime.now() + timedelta(hours=4) #timezone from Brasilia
                    end =  start + timedelta(days=1)
                    end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
                    result = c_handler.WeekDaySchedule(-2,start,end)
                    if result:
                        self.bot.speak(userkey, result)
                        step =  4 #self.response.out.write('<goto=7>')
                    else:
                        self.bot.speak(userkey,'Nenhuma atividade pendente encontrada para %s !' % msg)
                        step = 4  #self.response.out.write('<goto=4>')
                elif msg in ['amanha']:
                    start = datetime.now() + timedelta(days=1)  #timezone from Brasilia
                    start = datetime(day=start.day,month=start.month,year=start.year,second=0,minute=0,hour=3)
                    end = start + timedelta(days=1)
                    end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
                    result = c_handler.WeekDaySchedule(-1,start,end)
                    if result:
                        self.bot.speak(userkey, result)
                        step =  4 #self.response.out.write('<goto=7>')
                    else:
                        self.bot.speak(userkey,'Nenhuma atividade pendente encontrada para %s !' % msg)  
                elif msg in ['quarta', 'quinta']:
                    start = datetime.now().weekday()
                    if msg == 'quarta':
                        week_day = 2
                    elif msg == 'quinta': 
                        week_day = 3                        

                    start = datetime.now() + timedelta(days=days)  #timezone from Brasilia
                    start = datetime(day=start.day,month=start.month,year=start.year,second=0,minute=0,hour=3)
                    end = start + timedelta(days=1)
                    end = datetime(year=end.year,month=end.month,day=end.day,second=0,minute=0,hour=3)
                    result = c_handler.WeekDaySchedule(msg,start,end)
                    if result:
                        self.bot.speak(userkey, result)
                        step =  4 #self.response.out.write('<goto=7>')
                    else:
                        self.bot.speak(userkey,'Nenhuma atividade pendente encontrada para próximo(a) %s !' % msg)  

                if i == 0:
                    result = c_handler.dateQuery(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
                    self.assertEquals(len(result.entry),4)
                elif i == 1:
                    result = c_handler.dateQuery(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S'))
                    self.assertEquals(len(result.entry),5)


            
if __name__ == '__main__':
    unittest.main()
    