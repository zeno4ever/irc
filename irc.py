#!/usr/bin/python
'Botje voor tkkrlab, status van de space'

## Date : 30-4-2011
## Dave Borghuis
## V1.2
## 23-04-2011 Dave Added help function
## 03-05-2011 Dave Added redirect to sterr to file (to catch errors)
## 16-06-2011 Dave Added guard for disconnect,
##                 !led command to update matrix
##                  fix private messages to tkkrlabbot
## 13-12-2011 Dave Added Random quote function
## 01-04-2012 Dave Timeout after 5 min, try to reconnect
## 08-04-2012 Dave Added function for LEd board
## 21-06-2012 Jurjen Data cleanuo
## 22-06-2012 Dave added topic change
## 23=06-2012 Dave added test mode
## https://gist.github.com/676306 voorbeeld nonblcking


import socket
import httplib
import urllib
import pytz
import random
import time
import datetime
import sys

irc_network = 'irc.freenode.net'
bot_owner = 'tkkrlab'
nick_name = 'tkkrlab'
irc_channel = '#tkkrlab'
irc_port = 6667

lockname = 'Lock-O-Matic'
statusfile = 'status.txt'
testmode = False
blockmode = 1
irc_buffer = ''
#irc_buffer = None
lastledupdate = time.time()

if (len(sys.argv) > 1) and sys.argv[1] == 'test':
    nick_name = 'tkkrlabtest'
    irc_channel = '#tkkrlabtest'
    statusfile = 'status2.txt'
    irc_network = 'chat.freenode.net'
    lockname = 'lockomagic'
    testmode = True
    print 'TEST MODE'
    blockmode = 1
else:
    print 'Live Mode'
    fsock = open('irc_error.log','w')
    sys.stderr = fsock
    #sys.stdout = fsock

def irc_connect():
    'Connect to a channel'
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if blockmode == 0:
        conn.setblocking(0)
    else:
        conn.setblocking(1)
        conn.settimeout(500)
    conn.connect((irc_network, irc_port))
    conn.send('NICK ' + nick_name + '\r\n')
    conn.send('USER Tkkrlab Tkkrlab Tkkrlab :TkkrLab\r\n')
    conn.send('PRIVMSG NickServ :IDENTIFY tkkrlab1337\r\n')
    conn.send('JOIN ' + irc_channel + '\r\n')
    return conn

def read_data():
    'Read a string from the irc server'
    global irc
    global irc_buffer
    line = ''
    try:
        if blockmode == 1:
            line = irc.recv(4096)
        else:
            idata = irc.recv(4096)
            irc_buffer += idata
            line, irc_buffer = irc_buffer.split('\r\n',1)
        if testmode:
            print line
        if line.find('PING') != -1:
            irc.send('PONG ' + line.split()[1] + '\r\n')
            return None
        if line.find('PRIVMSG') != -1:
            nick = line.split('!')[0].replace(':', '')
            message = line.split('PRIVMSG')[1]
            message = ''.join(message.split(':')[1:])
            destination = ''.join(line.split(' ')[2])
            return (nick, message, destination)
        if line.find('NOTICE') !=-1:
            nick = line.split('!')[0].replace(':', '')
            message = line.split('NOTICE')[1]
            message = ''.join(message.split(':')[1:])
            destination = ''.join(line.split(' ')[2])
            return (nick, message, destination)
        return None
    except socket.timeout:
        irc.close()
        irc = irc_connect()
        return None

def msg(s,destination):
    'Send a message to the current channel'
    irc.send('PRIVMSG ' + destination + ' :' + s + '\r\n')

def settopic(topic):
    'Set topic in curren channel'
    irc.send('TOPIC '+ irc_channel + ' :' + topic +' | See our activities on http://bit.ly/AsJMNc\r\n')
    irc.send('PRIVMSG '+ irc_channel + ' :' + topic + '\r\n')

def random_quote():
    'Read a quote from a text file'
    try:
        with open("quotes.txt") as fd:
            return random.choice(fd.readlines())
    except IOError:
        return 'No quote file found'

def status():
    try:
        'Get status/date from file'
        conn = httplib.HTTPConnection("www.tkkrlab.nl")
        conn.request("GET", "/state/state", None, {"Accept": "text/plain"})
        r = conn.getresponse()
        #print r.status, r.reason, r.getheader("Location")
        tkstatus = r.read()
        conn.close()
        head = r.getheader("Last-Modified")
        if head == None:
            return 'We are ' + tkstatus
        ptime = datetime.datetime.strptime(head, "%a, %d %b %Y %H:%M:%S %Z")
        ptime = ptime.replace(tzinfo=pytz.timezone("GMT"))
        ptime = ptime.astimezone(pytz.timezone("Europe/Amsterdam"))
        return 'We are ' + tkstatus + ' ' + ptime.strftime("%a, %d %b %Y %H:%M:%S")
    except:
        return 'Sorry cant get status, try later again (Error:' + sys.exc_info()[0]+ ')'

def gettime():
    return time.strftime("%H:%M", time.localtime())

def checklocalstatus(tkstatus):
    try:
        with open(statusfile) as fd:
            newstatus = fd.readline().strip()
            if tkstatus == None:
                tkstatus = newstatus
            if tkstatus != newstatus:
                if newstatus == '1':
                    settopic('We zijn Open')
                    print 'Topic : Open'
                else:
                    settopic('We zijn Dicht')
                    print 'Topic : Dicht'
                tkstatus = newstatus
        return tkstatus
    except IOError:
        return 'No status file found'

def sendled(led_message):
    'Send a command to the led board'
    conn = httplib.HTTPConnection("192.168.100.250")
    url = "/~manson/led/txt.php?text=" + urllib.quote(led_message[:85])
    conn.request("GET", url)
    response = conn.getresponse()
    res = response.status
    conn.close()
    lastledupdate = time.time()
    if res != 200:
        return 'Error:' + res + ' - ' + response.reason
    else:
        return ''

irc = irc_connect()
tkstatus = checklocalstatus(None)
username = ''
ledtimeout = 15*60
timer = 0
while True:
    time.sleep(0.3)
    if testmode:
        print '-- time --'
        print 'Tijd is'
        print time.time()
        print 'timeout is '
        print ledtimeout
        print 'last update'
        print lastledupdate
    if lastledupdate + ledtimeout < time.time():
       lastledupdate = time.time()
       timer = 0
       print 'led timeout'
       sendled(' ')
    tkstatus = checklocalstatus(tkstatus)
    data = read_data()
    if data != None:
        (nick, message, destination) = data
        if testmode:
            print '--------- spit -------'
            print data
            print 'name:'+ nick + ' dest:' + destination + ' Message:' + message
            print 'lockname = '+lockname
            print 'staus = '+tkstatus
        if destination == nick_name:
            destination = nick
        else:
            destination = irc_channel
        # Funtions to do when open
        if tkstatus=='1':
            if (message.find('entered the space') >1 or message.find('is near the space')>1 ) and nick==lockname:
                if message.find('entered the space') >1:
                    username = ' '.join(message.split(' ')[:-3])
                if message.find('is near the space')>1:
                    username = ' '.join(message.split(' ')[:-4])
                sendled(' Welcome @space '+username.center(16))
                #ledtimeout=300
                timer=0
            if message.startswith('!led '):
                ledmessage = message[message.index('!led') + 5:]
                msg('Led '+ sendled(ledmessage), destination)
                #ledtimeout=500
                timer=0
            if message.startswith('!time'):
                timer=1
            if timer==1:
                sendled(gettime().center(16))
        if tkstatus =='0' and message.startswith('!led '):
            msg('Sorry '+nick+', can only do this when space is open.',destination)
        if message.startswith('!status'):
            msg(status(),destination)
        if message.startswith('!quote'):
            msg('Quote: ' + random_quote(),destination)
        if message.startswith('!help'):
            msg('!quote: to get a random quote',destination)
            msg('!status: to get open/close status of the space',destination)
            msg('!led messge: put message on led matrix board',destination)
            msg('!time: put current time on led matrix board',destination)
            msg('!tkkrhelp: this message',destination)
            msg('See also my friends Lock-O-Matic and arcade 1943'
                ' (if he is around)',destination)
