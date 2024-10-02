# Telethon utility # pip install telethon
from telethon import TelegramClient, events
from telethon.tl.custom import Button

import configparser # Library for reading from a configuration file, # pip install configparser
import datetime # Library that we will need to get the day and time, # pip install datetime

import psycopg2
import time
import locale
import socket
import random
from dateutil.relativedelta import relativedelta

SERVER = "app.manzada.net"
WEBPORT = 80
TIMEOUT = 3
RETRY = 1
locale.setlocale(locale.LC_ALL, '')

#### Access credentials
config = configparser.ConfigParser() # Define the method to read the configuration file
config.read('config.ini') # read config.ini file

api_id = config.get('default','api_id') # get the api id
api_hash = config.get('default','api_hash') # get the api hash
BOT_TOKEN = config.get('default','BOT_TOKEN') # get the bot token

def tcpCheck(ip, port, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, int(port)))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except:
        return False
    finally:
        s.close()

def check_server(ip, port, timeout, retry):
    ipup = False
    for i in range(retry):
        if tcpCheck(ip, port, timeout):
            ipup = True
            break
        else:
            print("Tidak terhubung...")
            time.sleep(timeout)
    return ipup

def get_stat_server(nama):
    text=""
    if self.check_server(SERVER, WEBPORT, TIMEOUT, RETRY):
        resp_check=["Server [Online] :)", "Server [Online]. Tidak ada masalah di sisi server\
        \nJika kesulitan membuka web\n1.Cek jaringan internet\n2.Kurangi beban memory HP\
        \n3.Bersihkan cache chrome\n4.Off\On Mode pesawat\n5.Restart HP"]
        random.shuffle(resp_check)
        text=resp_check[0]
    else:
        text="Maaf {}. server sedang offline :(".format(nama)
    return text
    
def sql_query(sql):
    conn_serv=False
    record=False
    try:
        conn_serv=psycopg2.connect(user="offline",
                                   password="ra#asia",
                                   host=SERVER,
                                   port="5432",
                                   database="manzada")
        cursor=conn_serv.cursor()
        cursor.execute(sql)
        record=cursor.fetchall()
    except (Exception, psycopg2.Error) as error:
        print(error)
        return False
    finally:
        if(conn_serv):
            cursor.close()
            conn_serv.close()
            return record
                

# Create the client and the session called session_master. We start the session as the Bot (using bot_token)
client = TelegramClient('sessions/session_master', api_id, api_hash).start(bot_token=BOT_TOKEN)

# Define the /start command
@client.on(events.NewMessage(pattern='/(?i)start')) 
async def start(event):
    sender = await event.get_sender()
    SENDER = sender.id
    text = "Rin Bot 🤖 ready\nHello! I'm answering you from Telegram!"
    await client.send_message(SENDER, text, parse_mode="HTML")

### First command, get the time and day
@client.on(events.NewMessage(pattern='/(?i)time')) 
async def time(event):
    # Get the sender of the message
    sender = await event.get_sender()
    SENDER = sender.id
    text = "Received! Day and time: " + str(datetime.datetime.now())
    await client.send_message(SENDER, text, parse_mode="HTML")

@client.on(events.NewMessage(pattern='/(?i)server')) 
async def time(event):
    # Get the sender of the message
    sender = await event.get_sender()
    SENDER = sender.id
    text = get_stat_server(nama)
    await client.send_message(SENDER, text, parse_mode="HTML")

@client.on(events.NewMessage(pattern='/(?i)omzet')) 
async def time(event):
    # Get the sender of the message
    sender = await event.get_sender()
    SENDER = sender.id
    text = get_omzet()
    await client.send_message(SENDER, text, parse_mode="HTML")


### MAIN
if __name__ == '__main__':
    print("Bot Started!")
    client.run_until_disconnected()
