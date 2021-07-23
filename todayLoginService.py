import re
from urllib.parse import urlparse

import requests
from urllib3.exceptions import InsecureRequestWarning

from login.casLogin import casLogin
from login.iapLogin import iapLogin
from login.henuLogin import henuLogin
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class TodayLoginService:
    # 初始化本地登录类
    def __init__(self, userInfo):
        if None == userInfo['username'] or '' == userInfo['username'] or None == userInfo['password'] or '' == userInfo['password'] or None == userInfo['schoolName'] or '' == userInfo['schoolName']:
            raise Exception('初始化类失败，请键入完整的参数（用户名，密码，学校名称）')
        print(f'当前正在签到的用户信息：{userInfo}')
        self.ua = userInfo['ua']
        self.username = userInfo['username']
        self.password = userInfo['password']
        self.schoolName = userInfo['schoolName']
        self.session = requests.session()
        headers = {
            'User-Agent': self.ua,
        }
        self.session.headers = headers
        self.login_url = ''
        self.host = ''
        self.login_host =''
        self.loginEntity = None

    # 通过学校名称借助api获取学校的登陆url
    def getLoginUrlBySchoolName(self):
        schools = self.session.get('https://mobile.campushoy.com/v6/config/guest/tenant/list', verify=False).json()[
            'data']
        flag = True
        for item in schools:
            if item['name'] == self.schoolName:
                if item['joinType'] == 'NONE':
                    raise Exception(self.schoolName + '未加入今日校园，请检查...')
                flag = False
                params = {
                    'ids': item['id']
                }
                data = self.session.get('https://mobile.campushoy.com/v6/config/guest/tenant/info', params=params,
                                        verify=False, ).json()['data'][0]
                joinType = data['joinType']
                idsUrl = data['idsUrl']
                ampUrl = data['ampUrl']
                if 'campusphere' in ampUrl or 'cpdaily' in ampUrl:
                    self.host = re.findall('\w{4,5}\:\/\/.*?\/', ampUrl)[0]
                    status_code = 0
                    while status_code != 200:
                        newAmpUrl = self.session.get(ampUrl, allow_redirects=False, verify=False)
                        status_code = newAmpUrl.status_code
                        if 'Location' in newAmpUrl.headers:
                            ampUrl = newAmpUrl.headers['Location']
                    parse = urlparse(ampUrl)
                    host = parse.netloc
                    self.login_url = ampUrl
                    self.login_host = re.findall('\w{4,5}\:\/\/.*?\/', self.login_url)[0]
                ampUrl2 = data['ampUrl2']
                if 'campusphere' in ampUrl2 or 'cpdaily' in ampUrl2:
                    self.host = re.findall('\w{4,5}\:\/\/.*?\/', ampUrl2)[0]
                    parse = urlparse(ampUrl2)
                    host = parse.netloc
                    res = self.session.get(parse.scheme + '://' + host)
                    parse = urlparse(res.url)
                    self.login_url = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                    self.login_host = re.findall('\w{4,5}\:\/\/.*?\/', self.login_url)[0]

                break

    # 通过登陆url判断采用哪种登陆方式
    def checkLogin(self):
        print(f'使用的登录链接为：{self.login_url}')
        if self.login_url.find('/iap') != -1:
            self.loginEntity = iapLogin(self.username, self.password, self.login_url, self.login_host, self.session)
            self.session.cookies = self.loginEntity.login()
        elif self.login_url.find('henu.edu.cn') != -1:
            self.loginEntity = henuLogin(self.username, self.password, self.login_url, self.login_host, self.session)
            self.session.cookies = self.loginEntity.login()
        else:
            self.loginEntity = casLogin(self.username, self.password, self.login_url, self.login_host, self.session)
            self.session.cookies = self.loginEntity.login()
    # 本地化登陆
    def login(self):
        # 获取学校登陆地址
        self.getLoginUrlBySchoolName()
        self.checkLogin()
