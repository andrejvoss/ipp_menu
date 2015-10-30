#import sys
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
#from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
import re
from datetime import timedelta
from datetime import datetime
import urllib2

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
    def __init__(self):
        self.days = []

    def add_pdf_to_menu(self, path):
        # Generate a general menu
        start_index = len(self.days)
        #Read the file
        text = parse_pdf(path)

        # Find all dates in the file
        dates = list(re.finditer('[0-9]{1,2}\.[0-9]{1,2}\.20[0-9]{2}', text))

        # Add dates to the menu
        for date in dates:
            dd = datetime.strptime(date.group(0), "%d.%m.%Y")
            self.add_day(dd)

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
                 self.days[start_index + i].add_dish(meal)

    def today(self):
        today = datetime.today().date()

        for day in self.days:
            if day.date == today:
                day.print_menu()


    def tomorrow(self):

        today = datetime.today().date()
        tomorrow = today + timedelta(days=1)

        found = False
        for day in self.days:
            if day.date == tomorrow:
                day.print_menu()
                found = True
        if not found:
            print "No menu for " + tomorrow.strftime("%d.%m.%Y")

    def add_day(self, date):
        day =day_menu(date)
        self.days.append(day)
        return day

class day_menu(object):
    def __init__(self, date):
        self.date = date.date()
        self.dishes = []

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
