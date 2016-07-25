#!/usr/bin/env python

import urllib2
import smtplib
import bs4
from local import secrets

class CraigslistDogFinder():
    def __init__(self, terms, fromAddr, toAddrs):
        self.terms = terms
        self.fromAddr = fromAddr
        self.toAddrs = toAddrs
        self.server = smtplib.SMTP()
        self.server.connect('smtp.gmail.com', 587)
        self.server.starttls()
        self.server.login(secrets.EMAIL, secrets.PASS)
        self.sentlinksFn = '/home/nick/src/dogfinder/sentlinks.txt'
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        self.fullMessage = []
    def read_sentlinks_file(self):
        sentlinksFile = open(self.sentlinksFn, 'r')
        sentLinks = sentlinksFile.read()
        self.sentLinks = sentLinks.split('\n')
    def get_post_urls(self, query):
        queryURL = 'https://eugene.craigslist.org/search/pet?query={}&postedToday=1'.format(query)
        response = self.opener.open(queryURL)
        mainPageSoup = bs4.BeautifulSoup(response.read(), 'html.parser')
        mydivs = mainPageSoup.find_all("div", { "class" : "rows" })
        postURLs = []
        for div in mydivs:
            links = div.findAll('a', {'class': 'hdrlnk'})
            for link in links:
                href = link.get('href')
                postURLs.append(href)
        return postURLs
    def make_full_links(self, partialLinks):
        '''
        Convert craigslist partial links (with local links relative) to full links
        '''
        fullLinks = []
        for link in partialLinks:
            if link[1]=='/': #The second char is a slash (two slash at beginning)
                fullLink = '{}{}'.format('https:', link)
            else:
                fullLink = '{}{}'.format('https://eugene.craigslist.org', link)
            fullLinks.append(fullLink)
        return fullLinks
    def remove_already_sent(self, links):
        '''
        Remove links found in the sentLinks file
        '''
        notSentYet = [link for link in links if link not in self.sentLinks]
        return notSentYet
    def send_email(self, message):
        '''
        Send a message to each email in self.toAddrs
        '''
        for toAddr in self.toAddrs:
            self.server.sendmail('nickponvert@gmail.com', toAddr, message)
    def write_new_links_to_sentlinks_file(self, newLinks):
        sentlinksFile = open(self.sentlinksFn, 'a')
        for url in newLinks:
            sentlinksFile.write('{}{}'.format(url,'\n'))
        sentlinksFile.close()
    def tear_down(self):
        '''
        Quit the email server
        '''
        self.server.quit()
    def process_query(self, query):
        #Re-read the sentlinks file
        self.read_sentlinks_file()
        #Get the post urls and convert to full links
        postURLs = self.get_post_urls(query)
        fullLinks = self.make_full_links(postURLs)
        #Remove links sent already
        notSentYet = self.remove_already_sent(fullLinks)
        #Write new links to the sentlinks file
        self.write_new_links_to_sentlinks_file(notSentYet)
        queryHeader = "New postings with the search term '{}' in the past hour".format(query)
        if notSentYet:
            self.fullMessage.append(queryHeader)
            for url in notSentYet:
                self.fullMessage.append(url)
    def process_all(self):
        for term in self.terms:
            self.process_query(term)
        if self.fullMessage:
            message = '\n'.join(self.fullMessage)
            self.send_email(message)
        self.tear_down()

if __name__=='__main__':

    #The search terms we want to use
    terms = ['lab', 'labrador', 'retreiver', 'puppy', 'pup', 'rottweiler', 'rotty', 'australian', 'shepherd', 'german', 'heeler']
    #Find those dogs
    dogfinder = CraigslistDogFinder(terms, 'nickponvert@gmail.com', ['nickponvert@gmail.com', 'nudibranch2@gmail.com'])
    dogfinder.process_all()
