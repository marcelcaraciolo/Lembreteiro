# -*- coding: utf-8 -*-
#!/usr/bin/env python
import string

import gdata.calendar.service
from datetime import datetime
from datetime import timedelta


HOJE = -2
AMANHA = -1


CONFIG_FILE = 'settings.txt'
f = map(string.strip,open(CONFIG_FILE).readlines())
email = f[1]
password = f[3]

class CalendarManager(object):
    
    def __init__(self,token=None):
        self.cal_client = gdata.calendar.service.CalendarService()
        self.cal_client.email =  email
        self.cal_client.password = password
        self.cal_client.source = 'lembreteiro-v0.1'
        self.cal_client.ProgrammaticLogin()

    def dateQuery(self, start_date=None, end_date=None):
        query = gdata.calendar.service.CalendarEventQuery('default', 'private', 
           'full')
        query.start_min = start_date
        query.start_max = end_date 
        feed = self.cal_client.CalendarQuery(query)
        return feed


    def DaySchedule(self,start_date, end_date):
        """ Os eventos para hoje são:
              X  em  Y às HH:MM. 
              Z  em  Z às HH:MM.
        """
        feed = self.dateQuery(start_date,end_date)
        msg = ""
        entries = sorted(feed.entry,key=lambda x: x.when[0].start_time)
        for i,event in enumerate(entries):
            if event.title.text:
                if i == 0:  msg+= 'Os eventos de hoje são:\n'
                msg += event.title.text
                if event.where[0].value_string:
                    msg +=  ' em  %s'  % event.where[0].value_string
                if event.when:
                    dt, _, us= event.when[0].start_time.partition(".")
                    dt2, _, us= event.when[0].end_time.partition(".")
                    start_time = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                    end_time = datetime.strptime(dt2, "%Y-%m-%dT%H:%M:%S")
                    msg += ' às %s até %s.' % (start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
                msg += '\n'
        return msg


    def HourSchedule(self,start_date, end_date):
        """ Os eventos para HH:MM são (procurar eventos no intervalo HH:00 até HH:59 do dia!)
              X  em  Y às HH:MM. 
              Z  em  Z às HH:MM.
        """

        dt_start = start_date.strftime('%Y-%m-%dT%H:%M:%S')
        dt_end =  end_date.strftime('%Y-%m-%dT%H:%M:%S')

        st_time = start_date - timedelta(hours=3)
        feed = self.dateQuery(dt_start,dt_end)
        msg = ""
        for i,event in enumerate(feed.entry):
            if event.title.text:
                if i == 0:  msg+= 'Os eventos para hora %s são:\n'  % st_time.strftime('%H:%M')
                msg += event.title.text
                if event.where[0].value_string:
                    msg +=  ' em  %s'  % event.where[0].value_string
                if event.when:
                    dt, _, us= event.when[0].start_time.partition(".")
                    dt2, _, us= event.when[0].end_time.partition(".")
                    start_time = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                    end_time = datetime.strptime(dt2, "%Y-%m-%dT%H:%M:%S")
                    if start_time < st_time:
                        msg +=  ' começou às %s e vai até %s. ' % (start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
                    else:
                        msg += ' às %s até %s.' % (start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
                msg += '\n'
        return msg
        
    def DateSchedule(self,start_date,end_date):
        """ Os eventos para DD/MM/YYYY são (procurar eventos para o dia todo DD/MM/YYYY)
              X  em  Y às HH:MM. 
              Z  em  Z às HH:MM.
        """
        dt_start = start_date.strftime('%Y-%m-%dT%H:%M:%S')
        dt_end =  end_date.strftime('%Y-%m-%dT%H:%M:%S')

        feed = self.dateQuery(dt_start,dt_end)

        entries = sorted(feed.entry,key=lambda x: x.when[0].start_time)
        msg = ""
        for i,event in enumerate(entries):
            if event.title.text:
                if i == 0:  msg+= 'Os eventos para o dia %s são:\n'  % start_date.strftime('%d/%m/%y')
                msg += event.title.text
                if event.where[0].value_string:
                    msg +=  ' em  %s'  % event.where[0].value_string
                if event.when:
                    dt, _, us= event.when[0].start_time.partition(".")
                    dt2, _, us= event.when[0].end_time.partition(".")
                    start_time = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                    end_time = datetime.strptime(dt2, "%Y-%m-%dT%H:%M:%S")
                    if start_time < start_date - timedelta(hours=3):
                        msg += '  comeeçou no dia %s às %s e vai até %s. ' % (start_time.strftime('%d/%m/%Y'), start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
                    else:
                        msg += ' às %s até %s.' % (start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
                    
                msg += '\n'
        return msg

        
    def WeekDaySchedule(self,day_text,start_date,end_date):
        """ Os eventos para DD/MM/YYYY são (procurar eventos para o dia todo DD/MM/YYYY)
              X  em  Y às HH:MM. 
              Z  em  Z às HH:MM.
        """
        if day_text == HOJE:
            dt_start = start_date.strftime('%Y-%m-%dT%H:%M:%S')
            dt_end =  end_date.strftime('%Y-%m-%dT%H:%M:%S')
            return self.DaySchedule(dt_start,dt_end)
        elif day_text == AMANHA:
            dt_start = start_date.strftime('%Y-%m-%dT%H:%M:%S')
            dt_end =  end_date.strftime('%Y-%m-%dT%H:%M:%S')

            feed = self.dateQuery(dt_start,dt_end)
            entries = sorted(feed.entry,key=lambda x: x.when[0].start_time)
            msg = ""
            for i,event in enumerate(entries):
                if event.title.text:
                    if i == 0:  msg+= 'Os eventos para amanhã são:\n'
                    msg += event.title.text
                    if event.where[0].value_string:
                        msg +=  ' em  %s'  % event.where[0].value_string
                    if event.when:
                        dt, _, us= event.when[0].start_time.partition(".")
                        dt2, _, us= event.when[0].end_time.partition(".")
                        start_time = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                        end_time = datetime.strptime(dt2, "%Y-%m-%dT%H:%M:%S")
                        if start_time < start_date- timedelta(hours=3):
                            msg += '  comeeçou no dia %s às %s e vai até %s. ' % (start_time.strftime('%d/%m/%Y'), start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
                        else:
                            msg += ' às %s até %s.' % (start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
                    msg += '\n'
            return msg 
        else:
            dt_start = start_date.strftime('%Y-%m-%dT%H:%M:%S')
            dt_end =  end_date.strftime('%Y-%m-%dT%H:%M:%S')

            feed = self.dateQuery(dt_start,dt_end)
            entries = sorted(feed.entry,key=lambda x: x.when[0].start_time)
            msg = ""
            for i,event in enumerate(entries):
                if event.title.text:
                    if i == 0:  msg+= 'Os eventos para próximo(a) %s são:\n' % day_text
                    msg += event.title.text
                    if event.where[0].value_string:
                        msg +=  ' em  %s'  % event.where[0].value_string
                    if event.when:
                        dt, _, us= event.when[0].start_time.partition(".")
                        dt2, _, us= event.when[0].end_time.partition(".")
                        start_time = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                        end_time = datetime.strptime(dt2, "%Y-%m-%dT%H:%M:%S")
                        print start_time,start_date
                        if start_time < start_date- timedelta(hours=3):
                            msg += '  comeeçou no dia %s às %s e vai até %s. ' % (start_time.strftime('%d/%m/%Y'), start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
                        else:
                            msg += ' às %s até %s.' % (start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
                    msg += '\n'
            return msg
        
    
