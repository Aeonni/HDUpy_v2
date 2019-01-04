import pandas as pd
from bs4 import BeautifulSoup
import random
import re
import time

class Time:
    Days = {
        1 : 31,
        2 : (28,29),
        3 : 31,
        4 : 30,
        5 : 31,
        6 : 30,
        7 : 31,
        8 : 31,
        9 : 30,
        10 : 31,
        11 : 30,
        12 : 31
    }
    def __init__(self,string):
        self.year = int(string[0:4])
        self.month = int(string[4:6])
        self.day = int(string[6:8])
        if self.month == 2:
            if self.year%4 == 0:
                self.days = self.Days[self.month][1]
            else:
                self.days = self.Days[self.month][0]
        else:
            self.days = self.Days[self.month]
    def add(self,num):
        if self.day+num <= self.days:
            self.day += num
        else:
            if self.month + 1 > 12:
                self.year += 1
                self.month = 1
                self.day = num - (self.days - self.day)
            else:
                self.month += 1
                self.day = num - (self.days - self.day)
        return str(self.year)+str("%02d"%self.month)+str("%02d"%self.day)

class GetGrades:
    def __init__(self, user):
        self.u = user
        self.data = pd.read_html(self.u.gotoPage('成绩查询'))[1]
        self.data = self.data.dropna(axis=1)
    def print(self):
        print(self.data)
    def save(self, form = 'excel'):
        if(form == 'txt'):
            pass
        else:
            path = "GradeOf_%s_%s.xlsx"%(self.u.username,self.data[0][1])
            self.data.to_excel(path)
            return path

class GetCal:
    def __init__(self, user, fd):
        self.firstday = fd

        self.u = user

        html = self.u.gotoPage('学生个人课表') #获取课程表网页

        soup = BeautifulSoup(html)

        self.data = [] # data 为课程表列表[[名称, 时间, 老师, 地点]...]

        for i in soup.find_all('td'):
            subj = []
            for j in i.contents:
                if('<' not in str(j)):
                    subj.append(str(j))
            if(len(subj)>3 and ('\t' not in subj[0])):
                if(len(subj) == 8):
                    self.data.append(subj[:4])
                    self.data.append(subj[4:8])
                elif(len(subj) == 12):
                    self.data.append(subj[:4])
                    self.data.append(subj[6:10])
                else:
                    self.data.append(subj[:4])
    def print(self):
        print(self.data)
    def save(self, filepath = None):
        self.dataConv()
        if(filepath == None):
            filepath = '%sCal.ics'%self.u.username

        calfile = open(filepath,"w", encoding='utf8')
        calfile.write('BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:Aeonni_HDUCalss2iCal ver.2.0\nX-WR-CALNAME:课程表\n') # ical文件头
        # 开始写入课程数据
        for each in self.icaldata:
            calfile.write('BEGIN:VEVENT\n')
            for i in each:
                calfile.write(i +'\n')
            calfile.write('CATEGORIES:课程\nCLASS:PUBLIC\nEND:VEVENT\n')
        # 课程数据写入结束
        calfile.write('END:VCALENDAR\n') # ical 文件尾
        calfile.close()
    def dataConv(self):
        K2NDict = {
            '一' : ('1','MO'),
            '二' : ('2','TU'),
            '三' : ('3','WE'),
            '四' : ('4','TH'),
            '五' : ('5','FR'),
            '六' : ('6','SA'),
            '日' : ('7','SU')
        }
        timetable = {
            '1':('0805','0850'),
            '2':('0855','0940'),
            '3':('1000','1045'),
            '4':('1050','1135'),
            '5':('1140','1225'),
            '6':('1330','1415'),
            '7':('1420','1505'),
            '8':('1515','1600'),
            '9':('1605','1650'),
            '10':('1830','1915'),
            '11':('1920','2005'),
            '12':('2010','2055')
        }
        self.icaldata = []
        a0 = []
        for i in self.data:
            a = re.findall(r'周(.+?)第(.+?)节{第(.+?)-(.+?)周}', i[1])
            if len(a) == 0:
                a = a0
            else:
                a0 = a
            cla_s = ''
            for n in a[0][1]:
                if n != ',':
                    cla_s += n
                else:
                    break
            cla_e = ''
            for n in a[0][1]:
                if n != ',':
                    cla_e += n
                else:
                    cla_e = ''
            week_s = int(a[0][2])
            week_e = int(a[0][3][0:2])

            interval = 1
            danorshuang = 0
            count = 0
            if '双' in a[0][3]:
                if week_s%2 != 0:
                    week_s += 1
                else:
                    pass
                if week_e%2 != 0:
                    week_e -= 1
                else:
                    pass
                while week_s+(count*2) <= week_e:
                    count += 1
                interval = 2
                danorshuang = 1
            elif '单' in a[0][3]:
                if week_s%2 == 0:
                    week_s += 1
                else:
                    pass
                if week_e%2 == 0:
                    week_e -= 1
                else:
                    pass
                while week_s+(count*2) <= week_e:
                    count += 1
                interval = 2
                danorshuang = 0
            else:
                while week_s+count <= week_e:
                    count += 1

            rrule = 'RRULE:FREQ=WEEKLY;BYDAY='+K2NDict[a[0][0]][1]+';INTERVAL='+str(interval)+';COUNT='+str(count)

            t = Time(self.firstday)
            d = t.add(int(K2NDict[a[0][0]][0])-1+(week_s-1)*7)
            start = 'DTSTART;TZID=Asia/Shanghai:'+d+'T'+timetable[cla_s][0]+'00'
            end = 'DTEND;TZID=Asia/Shanghai:'+d+'T'+timetable[cla_e][1]+'00'

            each = []
            each.append('UID:'+str(time.time())+str(random.choice('abcdefg&#%^*f'))+self.u.username)
            each.append('SUMMARY:'+i[0])
            each.append('LOCATION:'+i[3])
            each.append('DESCRIPTION:'+i[1]+'\n老师：'+i[2])
            each.append(rrule)
            each.append(start)
            each.append(end)
            self.icaldata.append(each)
        return self.icaldata

class GetSubj:
    def __init__(self, user):
        self.u = user
        html = self.u.gotoPage('全校性公选课')
        soup = BeautifulSoup(html)
        hidXNXQ = soup.find(id = "hidXNXQ")['value']
        vs = soup.find(id = "__VIEWSTATE")['value']
        ev = soup.find(id = '__EVENTVALIDATION')['value']
        postdata = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': vs,
            '__EVENTVALIDATION': ev,
            'ddl_kcxz': '',
            'ddl_ywyl': '',
            'ddl_kcgs': '',
            'ddl_xqbs': '1',
            'ddl_sksj': '',
            'TextBox1': '',
            'txtYz': '',
            'hidXNXQ': hidXNXQ,
        }
        self.html = self.u.post(self.u.Page['全校性公选课'], data = postdata).text
        self.data = pd.read_html(html)[0]
    def print(self):
        print(self.data)
    def save(self, form = 'excel'):
        if(form == 'txt'):
            pass
        else:
            path = "Subjects.xlsx"
            self.data.to_excel(path)
            return path
    def re(self):
        return self.html

# class BaoMin:
