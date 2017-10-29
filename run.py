#!/usr/bin/env python
import feedparser
import re
import os
from google.cloud import datastore
from datetime import datetime

rss_url = os.environ['RSS_URL']
d = feedparser.parse(rss_url)
# print d
# print len(d['entries']) #compte

# print d['entries'][0]['title'] #affiche le nom du torrent
# print d['entries'][0]['link']

def cleanTitle(title):
    m = re.search('([^S]+)([S0-9]{0,3})([E0-9]{0,3})',title)
    
    return {'name': m.group(1),'season': m.group(2),'episode': m.group(3)}

    # ([^S]+)([S0-9]{0,3})([E0-9]{0,3})

def checkIfPresentDB(link):
    # Create a Cloud Datastore client.
    datastore_client = datastore.Client()

    # query = datastore_client.query(kind='follow')
    # image_entities = list(query.fetch())


    query = datastore_client.query(kind='follow')
    query.add_filter('link', '=', link)
    # query.add_filter('done', '=', False)
    # query.add_filter('priority', '>=', 4)
    # query.order = ['-priority']
    results = list(query.fetch())
    
    print results

    if len(results) == 0:
        present = False
    else:
        present = True
    
    print present

    return present

def saveInDB(serieName, season, episode, link, fullName):

    datastore_client = datastore.Client()

    with datastore_client.transaction():
        # incomplete_key = datastore_client.key('follow')
        # task = datastore.Entity(key=incomplete_key)
        key = datastore_client.key('follow',link)
        task = datastore.Entity(key=key)

        task.update({
            'serie_name': serieName,
            'season': season,
            'episode': episode,
            'link': link,
            'full_name': fullName,
            'integer_dt': datetime.utcnow()
        })

        datastore_client.put(task)

def main():
    for entry in d.entries:
        clean = cleanTitle(entry.title)
        # print entry.link
        present = checkIfPresentDB(entry.link)

        if present == True:
            exit(0)
        else:
            saveInDB(clean['name'], clean['season'], clean['episode'],entry.link, entry.title )
            print 'save in db ' + entry.title
            # send email!
        
        
    # print clean['name'] + clean['season'] + clean['episode']

if __name__ == "__main__":
    main()
