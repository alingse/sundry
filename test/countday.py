#coding=utf-8
#2016.09.12

import unittest
import datetime
import random
import time

#init
month_days = [[31 for i in range(12)] for j in range(2)]
for m in [4,6,9,11]:
    month_days[0][m - 1] = 30
    month_days[1][m - 1] = 30
month_days[0][2 -1] = 28
month_days[1][2 -1] = 29


def dayOfYear(year, month, day):
    patch = 0
    #四年一闰，百年不闰，四百年再闰
    #4 yes,100 not,400 yes
    if year % 4 == 0:
        patch = 1
        if year %100 == 0:
            patch = 0
            if year % 400 == 0:
                patch = 1

    #check range
    if year == 0:
        raise Exception('year error')
    if month - 1 > 11:
        raise Exception('month error')
    if day > month_days[patch][month - 1]:
        raise Exception('days error')

    #just sum
    count = sum(month_days[patch][:month - 1]) + day    
    return count


class TestCount(unittest.TestCase):
    
    @staticmethod
    def py_day_of_year(year,month,day):
        '''
        this is calculate by python `datetime` module
        '''
        thisday = datetime.datetime(year,month,day)
        start = datetime.datetime(year,1,1)
        diff = thisday - start
        cnt = diff.days + 1
        return cnt

    def check(self,year,month,day):
        '''
        check ths function `dayOfYear` with `py_day_of_year`
        '''
        cnt = dayOfYear(year, month, day)
        pycnt = self.py_day_of_year(year,month,day)
        
        self.assertEqual(cnt,pycnt)

    #测试正常数据
    def test_normal(self):
        self.check(2016,9,12)

    #测试 今天数据
    def test_now(self):
        date = datetime.datetime.now().date()
        self.check(date.year,date.month,date.day)

    #测试随机数据
    def test_random(self):
        now = int(time.time())
        now = now + random.randint(-10*now,10*now)
        date = datetime.date.fromtimestamp(now)
        self.check(date.year,date.month,date.day)        

    #测试10w天数据
    def test_range(self,year=1000):
        day = datetime.timedelta(days=1)
        date = datetime.datetime(year,1,1)
        for i in range(100000):
            date += day
            self.check(date.year,date.month,date.day)


if __name__ == '__main__':
    unittest.main()