## Defines the functions that will be used in GoogleScrape3.py

from bs4 import BeautifulSoup as BS
import requests
import time
import random
import pickle
import os, re
from functools import wraps
import errno
import os
import signal



class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


def gather_urls(search_term, page_count): # Gathers page_count urls from Google
    r = requests.get('http://www.google.com/search?q=' + search_term)
    soup = BS(r.text, 'lxml')

    stop_str1 = 'Shop for ' + search_term + ' on Google'
    stop_str2 = 'Images for ' + search_term
    stop_list = [stop_str1, stop_str2]

    address_book = []
    for i in range(1, page_count + 1):
        start = (i - 1) * 10
        if start == 0:
            r = requests.get('http://www.google.com/search?q=' + search_term)
        else:
            r = requests.get('http://www.google.com/search?q=' + search_term + '&start=' + str(start))
        soup = BS(r.text, 'lxml')
        blue_links = soup('h3', class_ = 'r')
        for link in blue_links:
            if link.text not in stop_list:
                try:
                    href = link.a['href']
                except:
                    continue
                url = href.replace('/url?q=', '')
                url = re.sub('&sa=.*', '', url)
                if not re.search('/search\\?q=', url):
                    address_book.append(url)
        print('Page ' + str(i) + ' of Google urls gathered.')
        time.sleep(random.uniform(0, 5))

    return address_book

def text_clean(text): 
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    text = text.replace(',', '')


@timeout(30)
def retrieve_text(address_book):  # Scrapes the text from a list of urls
    fulltext = [] # initialize empty list
    trouble_child = [] # initialize list to find pages that don't work

    for x in range(len(address_book)):
        proceed = "y"
        try:
            r = requests.get(address_book[x])
            html = r.text
        except:
            trouble = address_book[x]
            trouble_child.append(trouble)
            proceed = "n"
            pass

        if proceed == "y":
            soup = BS(html, "lxml")
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text() # get text
            text_clean(text) # Puts the text in a useful format
            fulltext.append(text) # append element with text from page x
            print ("Page: %s, %s to go" %(x + 1, len(address_book) - x - 1))

    for i, string in enumerate(fulltext):
        fulltext[i] = ''.join([j if ord(j) < 128 else '' for j in string])

    with open("fulltext.p", "wb") as f:
        pickle.dump(fulltext, f)

    return trouble_child

def google_scrape(search_text, pages):
    """Writes the text of n pages of Google search results into fulltext.p.
    This effectively joins all the scraperfunctions into one big function."""
    # For logging
    start_time=time.time()
    # Setup
    BlenderPath = os.getenv('HOME') + '/Documents/Blender'
    os.chdir(BlenderPath)

    # Gather a list of urls generated by Google according to the search term
    address_book = gather_urls(search_text, pages)
    
    # Print the urls
    print(address_book)
    
    # Scrape the text from each page, clean it, and write it to a pickled file
    # ('fulltext.p'). Also returns a list of difficult web pages.
    # Prints logging information
    trouble_child = retrieve_text(address_book)
    if p == True:
        print ('Text from %i web pages scanned.' % (len(address_book)-len(trouble_child)))
        t=time.time()-start_time
        ts = t % 60
        tm = t // 60
        print ('----- %i minutes, %i seconds -----' % (tm, ts))
        if len(trouble_child) == 0:
            print ("All pages successfully scanned.")
        if len(trouble_child) == 1:
            print ("1 problem child: ", trouble_child)
        if len(trouble_child) > 1:
            print("%i problem children: " % len(trouble_child),  trouble_child)
