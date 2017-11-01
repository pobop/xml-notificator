#!/usr/bin/env python
import re
import os
import smtplib
import feedparser
from datetime import datetime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from google.cloud import datastore


def cleanTitle(title):

    searchReg = re.search('([^S]+)([S0-9]{0,3})([E0-9]{0,3})', title)

    return {'name': searchReg.group(1), 'season': searchReg.group(2), 'episode': searchReg.group(3)}


def checkIfPresentDB(link):

    datastore_client = datastore.Client()

    query = datastore_client.query(kind='follow')
    query.add_filter('link', '=', link)
    results = list(query.fetch())

    if len(results) == 0:
        present = False
    else:
        present = True

    return present


def saveInDB(serieName, season, episode, link, fullName):

    datastore_client = datastore.Client()

    with datastore_client.transaction():
        incomplete_key = datastore_client.key('follow')
        task = datastore.Entity(key=incomplete_key)
        # key = datastore_client.key('follow',link)
        # task = datastore.Entity(key=key)

        task.update({
            'serie_name': serieName,
            'season': season,
            'episode': episode,
            'link': link,
            'full_name': fullName,
            'integer_dt': datetime.utcnow()
        })

        datastore_client.put(task)


def sendEmail(name, season, episode, url):

    fromaddr = os.environ['EMAIL_FROM']
    toaddr = os.environ['EMAIL_TO']
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = 'Un nouvel episode est disponible'

    body = """
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>html title</title>        
        </head>
        <body>
        <table>
            <tr>
                <td>Serie</td>
                <td>Episode</td>
                <td>Season</td>
                <td>Link</td>
            </tr>
            <tr>
                <td>{0}</td>
                <td>{1}</td>
                <td>{2}</td>
                <td><a href={3}>link</a></td>
            </tr>
        </table>
        </body>
        """
    fullBody = body.format(name, season, episode, url)

    msg.attach(MIMEText(fullBody, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(fromaddr, os.environ['EMAIL_PWD'])
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()
    except:
        print('Fail to send email')
        exit(1)


def main():

    rss_url = os.environ['RSS_URL']
    d = feedparser.parse(rss_url)

    for entry in d.entries:
        clean = cleanTitle(entry.title)
        present = checkIfPresentDB(entry.link)
        
        if present is True:
            exit(0)
        else:
            saveInDB(clean['name'], clean['season'], clean['episode'], entry.link, entry.title)
            sendEmail(clean['name'], clean['season'], clean['episode'], entry.link)

if __name__ == "__main__":
    main()
