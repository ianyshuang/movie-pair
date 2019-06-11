from django.shortcuts import render, redirect
from .models import TopMovie, Movie
import math
import gspread
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials

def save_and_match(newMovie):
  auth_json_path = '/Users/ianyshuang/Desktop/django-movie/DjangoEnv/website/MovieTogether.json'
  gss_scopes = ['https://spreadsheets.google.com/feeds']
  # 連線
  credentials = ServiceAccountCredentials.from_json_keyfile_name(auth_json_path, gss_scopes)
  gss_client = gspread.authorize(credentials)
  # 開啟 Google Sheet 資料表
  spreadsheet_key = '1jew8de4bvuBUaw6Fdd12lUh6qVWF7UGST9oZevefhNk'
  sheet = gss_client.open_by_key(spreadsheet_key).sheet1
  # Google Sheet 資料表
  sheetValue = sheet.get_all_values()
  matchPartner = []
  match = 0
  for i in range(1, len(sheetValue)):
    if newMovie[1] == sheetValue[i][1] and newMovie[2] == sheetValue[i][2] and newMovie[3] == sheetValue[i][3]:
      matchPartner.append(newMovie)
      matchPartner.append(sheetValue[i])
      sheet.delete_row(i + 1)
      match = 1
      break
    else:
      if i == len(sheetValue) - 1:
          sheet.append_row(newMovie)
      continue

  if match == 1:
    chromedriver = '/Users/ianyshuang/Desktop/django-movie/DjangoEnv/website/chromedriver'
    driver = webdriver.Chrome(executable_path=chromedriver)
    driver.get('https://mail.google.com/mail/?tab=rm&ogbl')
    q = driver.find_element_by_name('identifier')
    q.send_keys('simonlin890327')
    q.send_keys(Keys.RETURN)
    driver.implicitly_wait(1)
    a = driver.find_element_by_name('password')
    a.send_keys('pbcproject')
    a.send_keys(Keys.RETURN)
    driver.implicitly_wait(1)

    b = driver.find_element_by_xpath("//*[@class='T-I J-J5-Ji T-I-KE L3']")
    b.click()
    c = driver.find_element_by_xpath("//*[@class='vO']")
    c.send_keys(matchPartner[0][0])
    driver.implicitly_wait(1)
    d = driver.find_element_by_xpath("//*[@class='aoT']")
    d.send_keys('配對成功')
    driver.implicitly_wait(1)
    e = driver.find_element_by_xpath("//*[@class='Am Al editable LW-avf']")
    e.send_keys('恭喜您與暱稱 ' + matchPartner[1][4] + ' ' + matchPartner[1][0] + ' 配對成功，您欲觀賞的電影為' +
                matchPartner[0][1] + '，時間為' + matchPartner[0][2] + '，地區為' + matchPartner[0][3] + '。' + '\n祝你們觀影愉快~' + '\n「' + matchPartner[1][5] + '」')
    driver.implicitly_wait(1)
    f = driver.find_element_by_xpath(
        "//*[@class='T-I J-J5-Ji aoO v7 T-I-atl L3']")
    f.click()
    time.sleep(5)

    b = driver.find_element_by_xpath("//*[@class='T-I J-J5-Ji T-I-KE L3']")
    b.click()
    c = driver.find_element_by_xpath("//*[@class='vO']")
    c.send_keys(matchPartner[1][0])
    driver.implicitly_wait(1)
    d = driver.find_element_by_xpath("//*[@class='aoT']")
    d.send_keys('配對成功')
    driver.implicitly_wait(1)
    e = driver.find_element_by_xpath("//*[@class='Am Al editable LW-avf']")
    e.send_keys('恭喜您與暱稱 ' + matchPartner[0][4] + ' ' + matchPartner[0][0] + ' 配對成功，您欲觀賞的電影為' + matchPartner[1][1] + '，時段為' + matchPartner[1][2] + '，地區為' + matchPartner[1][3] + '。' + '\n祝你們觀影愉快~' + '\n「' + matchPartner[0][5] + '」')
    driver.implicitly_wait(1)
    f = driver.find_element_by_xpath(
      "//*[@class='T-I J-J5-Ji aoO v7 T-I-atl L3']")
    f.click()

    time.sleep(5)
    driver.close()

def print_target(target):
  print(target)

def top(request):
  topMovies = list(TopMovie.objects.all())
  movies = []
  for top in topMovies:
    # 用 model 查詢的結果會是一個 querySet，可以把它迭代開來取得裡面的電影物件
    querySet = Movie.objects(name = top['name'])
    week_revenue = top['week_revenue']
    if querySet:
      for movie in querySet:
        movieObject = {'name': movie.name, 'imdb_score': movie.imdb_score, 'image_url': movie.image_url, 'length': movie.length, 'week_revenue': week_revenue, 'id': movie.id}
        movies.append(movieObject)
  return render(request, 'movie/top.html', { 'movies': movies })

def category(request):
  movies = []
  categories = []
  querySet = Movie.objects
  for movie in querySet:
    for category in movie.category:
      categories.append(category)
  categories = list(dict.fromkeys(categories)) # 將重複的類型去掉，得到所有電影類型

  for movie in querySet:
    movieObject = {'name': movie.name, 'category': movie.category, 'image_url': movie.image_url, 'id': movie.id}
    movies.append(movieObject)
  return render(request, 'movie/category.html', { 'movies': movies, 'categories': categories })

def detail(request, movie_id):
  querySet = Movie.objects(id = movie_id)
  for movie in querySet:
    if math.isnan(movie.imdb_score):
      movie.imdb_score = -1
    movieObject = {'name': movie.name, 'category': movie.category, 'release_date': movie.release_date, 'length': movie.length, 'imdb_score': movie.imdb_score, 'description': movie.description, 'image_url': movie.image_url, 'id': movie.id}
  return render(request, 'movie/detail.html', {'movie': movieObject })

def form(request, movie_id):
  querySet = Movie.objects(id = movie_id)
  for movie in querySet:
    movieObject = {'name': movie.name, 'image_url': movie.image_url, 'id': movie.id}
  return render(request, 'movie/form.html', {'movie': movieObject})

def submit(request, movie_id):
  # 從 request 中取出資料並放進 data
  email = request.POST['email']
  name = request.POST['name']
  description = request.POST['description']
  location = request.POST['location']
  time = request.POST['time']
  # 拿出電影名稱
  querySet = Movie.objects(id = movie_id)
  for movie in querySet:
    movieName = movie.name
  # 將所有資料放入 list 裡面
  newMovie = [email, movieName, time, location, name, description]
  # 開啟另一個 thread 來執行，避免耽誤 client 端 render
  t = threading.Thread(target = save_and_match, args = [newMovie])
  t.setDaemon(False)
  t.start()
  return redirect('/')