from django.db import models
from mongoengine import *
import requests
import pandas as pd
from openpyxl import load_workbook
from bs4 import BeautifulSoup
import urllib.request
from requests_html import HTMLSession

# It takes a yahoo website as input
# It returns a panda dataframe that contains lists of Chinese names and English names and schedule websites and movie websites and introductions
def yahooMovieParser(url):
  r = requests.get(url)
  web_content = r.text
  soup = BeautifulSoup(web_content,'lxml')
  #時刻表
  newMovie3 = soup.find_all('div',class_="release_btn color_btnbox")
  
  links = []
  for t in newMovie3:
    try:
      links.append(t.find('a',class_="btn_s_time gabtn")['href'])
    except:
      links.append(0)
  
  
  # 中英文片名
  newMovie2 = soup.find_all('div', class_ = "release_movie_name")
  NameCHs = [t.find('a', class_='gabtn').text.replace('\n','').replace(' ','') for t in newMovie2]
  NameENs = [t.find('div', class_='en').find('a').text.replace('\n','').replace(' ','') for t in newMovie2]
  
  #Movie website
  websites = [t.find('a', class_='gabtn')['href'] for t in newMovie2]
  
  # 電影介紹
  newMovie4 = soup.find_all('div',class_="release_text")
  Intros = [t.find('span').text.replace('\n','').replace('\r','').replace('\xa0','').replace(' ','') for t in newMovie4]
  #合併成data frame
  df = pd.DataFrame({
    'Name':NameCHs,
    'EnName':NameENs,
    'time': links,
    'Intro': Intros,
    'Web': websites
  })
  return df

#A function that take website as input
#It returns next webpage
def getNext(url):
  r = requests.get(url)
  web_content = r.text
  soup = BeautifulSoup(web_content,'lxml')
  pageInfo = soup.find('div', class_='page_numbox')
  tagA = pageInfo.find('li', class_="nexttxt").find('a')
  if tagA:
    return tagA['href']
  else:
    return None
    
#A function that take schedule website as input
#It returns a dictionary that store time
def get_schedule(html):
  schedule = {}
  for i in html.find('div.area_timebox'):
    city = i.text[0:2]
    theater_schedule = {}#It store theaters in a same city
    for theater in i.find('ul'):
      times = []
      t = theater.text
      t = t.split(' ')
      for x in range(len(t)):
        if x >0:
          times.append(t[x][-5:-1]+t[x][-1])#time as string
      theater_schedule[t[0]] = times#t[0] is theater       
    schedule[city] = theater_schedule
  return schedule

def get_type(time_url):
  #進到網頁拿html
  r = requests.get(time_url)
  web_content = r.text
  soup = BeautifulSoup(web_content,'lxml')
  info = soup.find('div', class_='level_name')
  info1 = soup.find_all('span')
  types = info.text.replace('\n','').replace(' ','')
  types = types.split('/')
  photo = soup.find('div', class_='movie_intro_foto').find('img')['src']
  has_imdb = 0#有無imdb
  for i in info1:
    if i.text[0:4] == 'IMDb':
      imdb = float(i.text[7:-1]+i.text[-1])
      has_imdb = 1
    if i.text[0:4] == '上映日期':
      date = i.text[5:-1]+i.text[-1]
    if len(i.text)>0:
      if i.text[0] == '片':
        length = i.text[6:-1]+i.text[-1]
  if has_imdb:
    return types,imdb,date,length,photo
  else:
    return types,-1,date,length,photo
  

connect('movie')

# Create your models here.
class TopMovie(Document):
  name = StringField(max_length = 100)
  week_revenue = IntField(default = 0)


class Movie(Document):
  name = StringField(max_length = 200, required = True)
  category = ListField(max_length = 10, required = True)
  release_date = StringField(max_length = 10, required = True)
  length = StringField(max_length = 10, required = True)
  imdb_score = FloatField()
  description = StringField(max_length = 100000)
  image_url = StringField()


topMovies = list(TopMovie.objects)
# 如果top_movie 這個 collcection 是空的，就重新寫入
if not topMovies:
  # 下載xlsx檔
  r = requests.get('https://www.tfi.org.tw/BoxOfficeBulletin/weekly')
  soup = BeautifulSoup(r.text, 'html.parser')
  source = soup.select("a.file")[1].attrs['onclick']
  index1 = source.find("'")
  index2 = source.find("'", index1+1)
  fileUrl = 'https://www.tfi.org.tw' + urllib.parse.quote(source[index1+1:index2])
  urllib.request.urlretrieve(fileUrl, './test.xlsx')

  # 載入 xlsx 檔案
  workbook = load_workbook('/Users/ianyshuang/Desktop/django-movie/DjangoEnv/website/test.xlsx')
  worksheet = workbook.active

  movieList = list(worksheet.rows) # 將每一列資料從 generator 轉成 list
  movieList.pop(0) # 去掉欄位名稱的第一列

  name_list = []
  week_revenue_list = []

  for row in movieList:
    name = row[2].value
    week_revenue = int(row[9].value)
    name_list.append(name)
    week_revenue_list.append(week_revenue)

  df = pd.DataFrame({
    'name': name_list,
    'week_revenue': week_revenue_list
  })

  df = df.sort_values('week_revenue', ascending = False)
  df = df.head(20)

  for index, row in df.iterrows():
    TopMovie.objects.create(name = row['name'], week_revenue = row['week_revenue']).save()

movies = list(Movie.objects)
if not movies:
  url = 'http://movies.yahoo.com.tw/movie_intheaters.html'
  urlList = []
  
  while url:
    urlList.append(url)
    url = getNext(url)

  MovieInfo = None
  for url in urlList:
    d1 = yahooMovieParser(url)
    if MovieInfo is None:
      MovieInfo = d1
    else:
      MovieInfo = MovieInfo.append(d1,ignore_index=True)
  #爬 電影種類 imdb分數 上映日期 電影長度 電影圖片網址
  types = []
  imdbs = []
  dates = []
  lengths = []
  photos = []
  for time_url in MovieInfo['Web']:
    type,imdb,date,length,photo = get_type(time_url)
    types.append(type)
    imdbs.append(imdb)#請注意，如果imdb為-1這代表查不到imdb
    dates.append(date)
    lengths.append(length)
    photos.append(photo)
  #併到dataframe
  MovieInfo['type'] = types
  MovieInfo['imdb'] = imdbs
  MovieInfo['release_date'] = dates
  MovieInfo['length'] = lengths
  MovieInfo['photo_website'] = photos#電影圖片網址


  Movielist = [] # Movie名稱陣列
  for i in range(len(MovieInfo)):
    Movielist.append(MovieInfo['Name'][i])  

  Count = 0
  Moviedict = {}	  #電影的dictionary

  for j in Movielist:
    Moviedict[j] = []
    Moviedict[j].append(MovieInfo['Name'][Count])       #中文名稱
    Moviedict[j].append(MovieInfo['type'][Count])                #類型
    Moviedict[j].append(MovieInfo['release_date'][Count])        #上映時間
    Moviedict[j].append(MovieInfo['length'][Count])              #長度
    Moviedict[j].append(MovieInfo['imdb'][Count])       #IMDB分數
    Moviedict[j].append(MovieInfo['Intro'][Count])      #簡介
    #Moviedict[j].append(MovieInfo['schedule'][Count])   #時間表
    Moviedict[j].append(MovieInfo['photo_website'][Count])   #圖片網址
    Count += 1

  for name, info in Moviedict.items():
    Movie(name = info[0], category = info[1], release_date = info[2], length = info[3] , imdb_score = float('nan') if info[4] == -1.0 else info[4], description = info[5], image_url = info[6]).save()
    