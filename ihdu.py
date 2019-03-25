import requests
# import pytesseract
import execjs
from bs4 import BeautifulSoup
from PIL import Image

# 设置 UA
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36'

class User:
	header = {
		"User-Agent" : UA,
	}
	CurrentPage = ''
	HomePage = ''
	SubPage = {}
	Page = {}
	def __init__(self, usn, pwd):
		self.username = usn # 保存用户名为 username
		self.password = pwd 
		self.s = requests.session() # 启动一个回话
		self.HomePage = 'http://jxgl.hdu.edu.cn/xs_main.aspx?xh=' + self.username
	def get(self, url, **kwargs):
		self.CurrentPage = url
		r = self.s.get(url, headers=self.header, **kwargs)
		self.SubPage = FindSubPage(r.text)
		return r

	def post(self, url, data=None, json=None, **kwargs):
		self.CurrentPage = url
		r = self.s.post(url, data=data, headers=self.header, **kwargs)
		self.SubPage = FindSubPage(r.text)
		return r

	def login(self):
		url = 'https://cas.hdu.edu.cn/cas/login?service=http://jxgl.hdu.edu.cn/default.aspx'
		CaptchaUrl = "http://cas.hdu.edu.cn/cas/Captcha.jpg"
		# 获取登录页面
		r = self.get('http://jxgl.hdu.edu.cn/index.aspx')

		soup = BeautifulSoup(BeautifulSoup(r.text,'lxml').find('script', id="password_template").text, 'lxml')

		postDict = dict(
			lt = soup.find('input', id='lt').attrs['value'],
			execution = soup.find('input', attrs={'name':'execution'}).attrs['value'],
			_eventId = soup.find('input', attrs={'name':'_eventId'}).attrs['value'],
			ul = len(self.username),
			pl = len(self.password),
			rsa = strEnc_psswd(self.username+self.password+soup.find('input', id='lt').attrs['value'])
		)

		# 尝试登录
		r = self.post(url, postDict)

		try:
			soup = BeautifulSoup(r.text, 'lxml')
			finalurl = eval(soup.find('script').text[11:-1])[0]
		except:
			print('Login Error!')
			return 500

		r = self.get('http://jxgl.hdu.edu.cn/'+finalurl)
		r = self.get(self.HomePage)
		self.Page = self.SubPage
		self.header['Referer'] = self.HomePage
		print("Login Success!")
		soup = BeautifulSoup(r.text,'lxml')
		self.name = soup.find('span', id='xhxm').text[:-2]
		print("User: " + self.name)
		return self.name

	def gotoSubPage(self, index):
		return self.get(self.SubPage[index]).text

	def gotoPage(self, index):
		return self.get(self.Page[index]).text

	def BackHome(self):
		return self.get(self.HomePage)

	def Logout(self):
		return self.get('http://jxgl.hdu.edu.cn/logout0.aspx')

def FindSubPage(html):
	soup = BeautifulSoup(html, 'lxml')
	urllist = {}
	for i in soup.find_all('a'):
		if('#' not in i['href']):
			if('http:' in i['href']):
				urllist[i.string] = UrlModify(i['href'])
			else:
				urllist[i.string] = 'http://jxgl.hdu.edu.cn/'+UrlModify(i['href'])
	return urllist

def UrlModify(url):
	db = ('0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F')
	str = ''
	temp = url.encode('gb2312')
	loop = 0
	i = 0 # 计算汉字数
	stat = 0
	while i < len(temp):
		while(temp[i]>128):
			str += '%'
			str += db[int(temp[i]/16)]
			str += db[int(temp[i]%16)]
			i += 1
		if(stat == 0 and int((i-loop)/2) != 0):
			loop += int((i-loop)/2)
			stat = 1
		str += url[loop]
		loop += 1
		i += 1
	return str


def MainPageTags(tag):
	return tag.has_attr('class')

def get_js():
	while True:
		try:
			f = open("des.js", 'r', encoding='utf-8') # 打开JS文件
			break
		except:
			print('Downloading des.js ...')
			try:
				s = requests.get('http://cas.hdu.edu.cn/cas/comm/js/des.js').text
				with open("des.js", 'w') as f:
					f.write(s)
			except:
				print('Unexpexted Error in downloading des.js')
				exit()
	line = f.readline()
	htmlstr = ''
	while line:
		htmlstr = htmlstr+line
		line = f.readline()
	return htmlstr

def strEnc_psswd(data, key1 = '1', key2= '2', key3= '3'):
    jsstr = get_js()
    ctx = execjs.compile(jsstr) #加载JS文件
    return (ctx.call('strEnc', data, key1, key2, key3))  #调用js方法

def strDec_passwd(data, key1 = '1', key2= '2', key3 = '3'):
    jsstr = get_js()
    ctx = execjs.compile(jsstr) #加载JS文件
    return (ctx.call('strDec', data, key1, key2, key3))  #调用js方法