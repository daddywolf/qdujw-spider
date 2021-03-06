# -*- coding: utf-8 -*-

from PIL import Image
import io
import re
import getpass
import requests
import pytesseract
from lxml import etree
from prettytable import PrettyTable


class qdujw:
    def __init__(self):
        self.userid = 0
        self.s = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36'
        }

    # 教务登录
    def login(self):
        global sid, passwd, jw
        loginurl = 'http://jw.qdu.edu.cn/academic/j_acegi_security_check'
        codeurl = 'http://jw.qdu.edu.cn/academic/getCaptcha.do'
        userurl = 'http://jw.qdu.edu.cn/academic/showPersonalInfo.do'

        # 验证码
        code = self.s.get(codeurl, headers=self.headers, stream=True)
        img = Image.open(io.BytesIO(code.content))

        # 降噪
        threshold = 140
        table = []
        for i in range(256):
            if i < threshold:
                table.append(0)
            else:
                table.append(1)

        # 将彩色图像转换为灰度图像
        imgry = img.convert('L')

        # 讲图像中噪声去除
        out = imgry.point(table, '1')

        codetext = pytesseract.image_to_string(out, config='digits')

        # 去除空格，将.替换为0
        codetext = codetext.replace(' ', '')
        codetext = codetext.replace('.', '0')

        # 登录
        postdata = {
            'j_username': sid,
            'j_password': passwd,
            'j_captcha': codetext
        }
        r = self.s.post(loginurl, postdata)

        # 密码错误
        if re.search(u'\u5bc6\u7801\u4e0d\u5339\u914d', r.text):
            print sid + ' 密码不匹配!'
            print
            choice = raw_input('请选择(1.重新输入 2.退出)：')
            if choice == '1':
                sid = raw_input('学号：')
                passwd = getpass.getpass('密码：')
            else:
                exit()
            jw.login()

        # 用户名不存在
        elif re.search(u'\u4e0d\u5b58\u5728', r.text):
            print sid + ' 用户名不存在!'
            print
            choice = raw_input('请选择(1.重新输入 2.退出)：')
            if choice == '1':
                sid = raw_input('学号：')
                passwd = getpass.getpass('密码：')
            else:
                exit()
            jw.login()

        # 验证码错误
        elif re.search(u'\u9a8c\u8bc1\u7801\u4e0d\u6b63\u786e', r.text):
            print '正在登录，请耐心等待......'
            jw.login()

        # 成功
        else:
            userpage = self.s.get(userurl).content
            name = etree.HTML(userpage.decode(
                'utf-8', 'ignore')).xpath('/html/body/center/table[1]/tr[1]/td[2]/text()')
            for n in name:
                name = n.encode('utf-8')
            userid = re.findall(b'.*?userid=(.*?)"', userpage, re.S)
            for i in userid:
                self.userid = self.userid * 10 + int(i)
            print name + '登录成功！'

    # 查询成绩
    def scores(self):
        print '======= 成绩查询 ========'
        print
        year = raw_input('请输入查询学年: ')
        term = raw_input('春季学期输入[1],秋季学期输入[2]: ')
        scoresurl = 'http://jw.qdu.edu.cn/academic/manager/score/studentOwnScore.do'

        # 字符串计算  eval()
        postdata = {
            'year': eval(year + '-' + '1980'),
            'term': term,
            'para': '0'
        }
        scorespage = self.s.post(scoresurl, postdata).content
        aa = '<td>' + year + \
            '[\s\S]*?<td>[\s\S]*?<td>(.*?)[\s].*?</td>[\s\S]*?</td>[\s\S]*?<td>(.*?)[\s].*?</td>[\s\S]*?</td>[\s\S]*?</td>[\s\S]*?</td>[\s\S]*?</td>[\s\S]*?</td>[\s\S]*?</td>'

        # str转types  .encode(encoding="utf-8")
        scores = re.findall(aa.encode(encoding="utf-8"), scorespage, re.S)
        print
        print '======= 考试成绩 ========'
        for s in scores:
            print
            print s[0] + ' : ' + s[1]

    # 查询课表
    def kebiao(self):
        print '======= 课表查询 ========'
        print
        year = raw_input('请输入查询学年: ')
        term = raw_input('春季学期输入[1],秋季学期输入[2]: ')
        print

        # 使用 PrettyTable 打印表格
        x = PrettyTable(["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        x.padding_width = 1
        get = {
            'id': self.userid,
            'yearid': eval(year + '-' + '1980'),
            'termid': term,
            'timetableType': 'STUDENT',
            'sectionType': 'COMBINE'
        }

        kb = self.s.get(
            'http://jw.qdu.edu.cn/academic/manager/coursearrange/showTimetable.do', params=get)
        html = etree.HTML(kb.content)

        kb = html.xpath('//*[@id="timetable"]//*[@class="center"]')
        i = 0
        list = []
        list1 = ['', '', '', '', '', '', '']
        for k in kb:
            # print k.xpath('string()').encode('utf-8')

            # 通过 list 将课程信息添加到 PrettyTable 中
            if i < 7:
                list.append(
                    k.text.split(';')[0].replace('<<', '').replace('>>', ''))
                i += 1
                if i == 7:
                    # 上下显示一行空白，方便阅读
                    x.add_row(list1)
                    x.add_row(list)
                    x.add_row(list1)
                    list = []
                    i = 0
        print x

    # 教务通知
    def news(self):
        newsurl = requests.get(
            'http://jw.qdu.edu.cn/homepage/infoArticleList.do;jsessionid=E06A6E2B5FA3F797FAB8FA5F6331AC92?columnId=358')
        html = etree.HTML(newsurl.content.decode('utf-8', 'ignore'))
        news = html.xpath('//*[@id="thirdcontent"]/div[2]/ul/li/div/a')
        for new in news:
            print new.xpath('string(.)').encode('utf-8').replace(' ', '').replace('\n', '')
            print 'http://jw.qdu.edu.cn/homepage/' + new.attrib['href']
            print

    # 个人信息
    def user(self):
        print '======= 个人信息 ========'
        print
        user = self.s.get('http://jw.qdu.edu.cn/academic/showPersonalInfo.do')
        html = etree.HTML(user.content.decode('utf-8', 'ignore'))
        for n in html.xpath('/html/body/center/table[1]/tr[1]/td[2]/text()'):
            print '姓名: ' + n.encode('utf-8')
        for n in html.xpath('/html/body/center/table[1]/tr[2]/td[1]/text()'):
            print '院系: ' + n.encode('utf-8')
        for n in html.xpath('/html/body/center/table[1]/tr[2]/td[2]/text()'):
            print '专业: ' + n.encode('utf-8')
        for n in html.xpath('/html/body/center/table[1]/tr[4]/td[1]/text()'):
            print '年级: ' + n.encode('utf-8')
        for n in html.xpath('/html/body/center/table[1]/tr[4]/td[2]/text()'):
            print '班级: ' + n.encode('utf-8')

jw = qdujw()
print '======== 教务通知 ========'
jw.news()
print

print '======== 登录教务系统 ========'

# 学号和密码
print '请输入学号和密码'
sid = raw_input('学号：')
passwd = getpass.getpass('密码：')

jw.login()

while 1:
    print
    print '======== 青岛大学教务系统 ========'
    print
    print '[1]查询成绩'
    print '[2]查询课表'
    print '[3]个人信息'
    print '[4]退出'
    print
    choice = raw_input('请选择: ')
    print
    if choice == '1':
        jw.scores()
    elif choice == '2':
        jw.kebiao()
    elif choice == '3':
        jw.user()
    elif choice == '4':
        exit()
