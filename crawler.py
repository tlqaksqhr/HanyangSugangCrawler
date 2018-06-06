# -*- coding: utf-8 -*-

import requests
import json
import pickle
from functools import *
import time
import hashlib
import json
import re
import abc


class AbstractCrawler(metaclass=abc.ABCMeta):

	def __init__(self):
		pass

	def crawling(self):
		headers = self._make_header()
		url = self._make_url()
		payload = self._make_payload()
		data = self._request_query(url,header=headers,payload=payload)
		return data

	@abc.abstractmethod
	def _make_header(self):
		pass

	@abc.abstractmethod	
	def _make_url(self):
		pass

	@abc.abstractmethod
	def _make_payload(self):
		pass

	@abc.abstractmethod
	def _request_query(self,url,header={},payload={}):
		pass


class HanyangCrawlerTemplate(AbstractCrawler):

	def _get_token(self):
		url = "https://portal.hanyang.ac.kr/sugang/sulg.do"
		res = requests.get(url,verify=False)

		cookie = res.headers['Set-Cookie'].split(';')
		token = "{};{};".format(cookie[0],cookie[2][9:])

		return token

	def _make_header(self):
		headers = {}
		headers['Host']='portal.hanyang.ac.kr'
		headers['Connection']='keep-alive'
		headers['Accept']='application/json, text/javascript, */*; q=0.01'
		headers['Origin']='https://portal.hanyang.ac.kr'
		headers['X-Requested-With']='XMLHttpRequest'
		headers['Content-Type']='application/json+sua; charset=UTF-8'
		headers['Referer']='https://portal.hanyang.ac.kr/sugang/sulg.do'
		headers['Accept-Encoding']='gzip, deflate, br'
		headers['Accept-Language']='ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
		headers['Cookie']=self._get_token()
		return headers

	def _make_url(self):
		pass

	def _make_payload(self):
		pass

	def _request_query(self,url,header={},payload={}):
		pass


class LectureCrawler(HanyangCrawlerTemplate):

	def _make_url(self):
		url = "https://portal.hanyang.ac.kr/sugang/SgscAct/findSuupSearchSugangSiganpyo.do?pgmId=P310278&menuId=M006631&tk=e9068598524e004a4af6d96d34410fa56705e76bb2f7fc2df35729471b0f3b45"
		return url

	def _make_payload(self):
		payload = {"skipRows":"0","maxRows":"3200",
			"strLocaleGb":"ko","strIsSugangSys":"true","strDetailGb":"0",
			"notAppendQrys":"true","strSuupOprGb":"0","strJojik":"Y0000316",
			"strSuupYear":"2018","strSuupTerm":"10","strIsuGrade":"","strTsGangjwa":"",
			"strTsGangjwaAll":"0","strTsGangjwa3":"0","strIlbanCommonGb":"","strIsuGbCd":"",
			"strHaksuNo":"","strChgGwamok":"","strGwamok":"","strDaehak":"","strHakgwa":"",
			"strYeongyeok":""}
		return payload

	def _request_query(self,url,header={},payload={}):

		request_list = [(2017,10),(2017,15),(2017,20),(2017,25),(2018,10)]
		lecture_list = []

		for year,term in request_list:
			payload["strSuupTerm"]=str(term)
			payload["strSuupYear"]=str(year)
			r = requests.post(url,json=payload,verify=False,headers=header)

			data = r.json()["DS_SUUPGS03TTM01"][0]["list"]
			lecture_list += data

		return lecture_list

class AbstractParser(metaclass=abc.ABCMeta):
	
	def __init__(self,data):
		self.data = data
	
	@abc.abstractmethod
	def parse(self):
		pass


class LectureParser(AbstractParser):

	def parse(self):
		data = self.data
		table = {"10" : "1", "15" : "2", "20" : "3", "25" : "4"}
		course_name_buf_dict = {}

		for item in data:

			if "ERICA 대학" in item["banSosokNm"]:
				department = "교양"
			elif "전공" in item["isuGbNm"] or "기초필수" in item["isuGbNm"]:
				department = item["banSosokNm"]
			else:
				department = "교양"

			if item["isuTerm"] == "00":
				file_name = "{}_{}_{}.txt".format(department,item["isuGrade"],table["10"])
				if file_name in course_name_buf_dict:
					course_name_buf_dict[file_name] += course_name_line + "\n"
				else:
					course_name_buf_dict[file_name] = course_name_line + "\n"

				file_name = "{}_{}_{}.txt".format(department,item["isuGrade"],table["20"])
				if file_name in course_name_buf_dict:
					course_name_buf_dict[file_name] += course_name_line + "\n"
				else:
					course_name_buf_dict[file_name] = course_name_line + "\n"
			else:
				file_name = "{}_{}_{}.txt".format(department,item["isuGrade"],table[item["isuTerm"]])  # 학과_학년_학기.txt, 교양은 0
			
			course_name_line = item["gwamokNm"] + "\t" + item["gwamokEnm"]

			if file_name in course_name_buf_dict:
				course_name_buf_dict[file_name] += course_name_line + "\n"
			else:
				course_name_buf_dict[file_name] = course_name_line + "\n"

		return course_name_buf_dict

class AbstractSaver(metaclass=abc.ABCMeta):
	
	def __init__(self,data):
		self.data = data
	
	@abc.abstractmethod
	def save(self):
		pass

class LectureSaver(AbstractSaver):
	
	def save(self):
		path = "hyu_course_info/"
		data = self.data
		for file_name in data:
			name = path + file_name
			with open(name, 'wt', encoding='UTF8') as handle:
				handle.write(self.data[file_name])


class Scrapper():

	def __init__(self,crawler,parser,saver):
		self.crawler = crawler
		self.parser = parser
		self.saver = saver

	def scrapping(self):
		crawler = self.crawler()
		data = crawler.crawling()
		parser = self.parser(data)
		parsed_data = parser.parse()
		saver = self.saver(parsed_data)
		saver.save()


scrap = Scrapper(LectureCrawler,LectureParser,LectureSaver)
scrap.scrapping()