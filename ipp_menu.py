#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (C) 2015  Jörg Encke
This file is part of ipp_menu

auditory_brain is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

auditory_brain is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ipp_menu.  If not, see <http://www.gnu.org/licenses/>.
'''

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
import re
from datetime import timedelta
from datetime import datetime
import urllib2
import pickle as pkl
import os

class TextReciver(object):
    def __init__(self):
        self.text = ''

    def write(self, text):
        self.text += text


def parse_pdf(file_name):
    # input option
    password = ''
    pagenos = set()
    maxpages = 0
    # output option
    imagewriter = None
    rotation = 0
    codec = 'utf-8'
    caching = True
    laparams = LAParams()
    rsrcmgr = PDFResourceManager(caching=caching)
    outfp = TextReciver()
    device = TextConverter(rsrcmgr, outfp, codec=codec, laparams=laparams, imagewriter=imagewriter)

    for fname in [file_name]:
        fp = file(fname, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(fp, pagenos,
                                      maxpages=maxpages, password=password,
                                      caching=caching, check_extractable=True):
            page.rotate = (page.rotate+rotation) % 360
            interpreter.process_page(page)
        fp.close()
    device.close()
    return outfp.text


class Menu(object):
    def __init__(self, load_old=True):
        self.days = {}

        if load_old:
            self.load_old_dates()

    def load_old_dates(self):
        for root, dirs, files in os.walk('./tmp'):
            for name in files:
                if name.endswith((".pkl")):
                   fl = open(os.path.join(root, name), 'r')
                   date = pkl.load(fl)
                   self.days[date.date] = date
                   fl.close

    def add_pdf_to_menu(self, path, store=True):
        # Generate a general menu
        start_index = len(self.days)
        #Read the file
        text = parse_pdf(path)

        # Find all dates in the file
        dates = list(re.finditer('[0-9]{1,2}\.[0-9]{1,2}\.20[0-9]{2}', text))

        day_list = []
        # Add dates to the menu
        for date in dates:
            dd = datetime.strptime(date.group(0), "%d.%m.%Y")
            day_list.append(self.add_day(dd))

        #extract the text between the date entries
        text_pos = [d.start() for d in dates] + [len(text)]
        date_blocks = []
        for i in range(len(text_pos) - 1):
            date_blocks.append(text[text_pos[i]:text_pos[i+1]])

        # Extract the single menus
        for i, db in enumerate(date_blocks):
            meals = re.findall('(\n[0-9]\.[A-z| ].*)(\n +.*)?', db)
            meals = [(m[0] + m[1]).strip('\n') for m in meals]

            for meal in meals:
                 day_list[i].add_dish(meal)

        if store:
            for i in day_list:
                i.save_day()

    def today(self):
        today = datetime.today().date()

        if today in self.days:
            self.days[today].print_menu()
        else:
            print "No menu for " + tomorrow.strftime("%d.%m.%Y")

    def tomorrow(self):

        today = datetime.today().date()
        tomorrow = today + timedelta(days=1)

        if tomorrow in self.days:
            self.days[today].print_menu()
        else:
            print "No menu for " + tomorrow.strftime("%d.%m.%Y")

    def add_day(self, date):
        day = day_menu(date)
        self.days[date.date()] = day
        return day

    def find_in_menu(self, string):

        found_in = []
        for k, i in self.days.iteritems():
            for d in i.dishes:
                if string.lower() in d.lower():
                    found_in.append(i)
        return found_in



class day_menu(object):
    def __init__(self, date):
        self.date = date.date()
        self.dishes = []

    def save_day(self):
        filename = self.date.strftime("./tmp/%Y_%m_%d.pkl")
        fl = open(filename, 'w')
        pkl.dump(self, fl)
        fl.close()

    def add_dish(self, dish_desciption):
        self.dishes.append(dish_desciption)

    def print_menu(self):
        for i in self.dishes:
            print i

    def __repr__(self):
        repr = "<Menu for the " + self.date.strftime("%d.%m.%Y") + ">"
        return repr


menu = Menu()

link = 'http://betriebsrestaurant-gmbh.de/index.php?id=91'
response = urllib2.urlopen(link)
html = response.read()

first_part = 'http://betriebsrestaurant-gmbh.de/'
pdf_links = re.findall('".*IPP.*.pdf"', html)
pdf_links = [first_part + f[1:-1] for f in pdf_links]


for pdf in pdf_links:
    pdffile = urllib2.urlopen(pdf)
    output = open('temp.pdf','wb')
    output.write(pdffile.read())
    output.close()

    menu.add_pdf_to_menu('temp.pdf')
