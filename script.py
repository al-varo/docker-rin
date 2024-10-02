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

sql_omzet = "SELECT \
            x_user_id, \
            x_total_omzet, \
            round((coalesce(x_total_omzet,0)/\
            (CASE \
            WHEN x_user_id  = 5 THEN 3838464000 \
            WHEN x_user_id = 31 THEN 2632000000 \
            WHEN x_user_id = 7 THEN 2132480000 \
            WHEN x_user_id = 9 THEN 2531200000 \
            WHEN x_user_id = 44 THEN 1442560000 \
            WHEN x_user_id = 6 THEN 1288000000 \
            WHEN x_user_id = 56 THEN 2105600000 \
            WHEN x_user_id = 58 THEN 2132480000 \
            WHEN x_user_id = 59 THEN 1442560000 \
            WHEN x_user_id = 60 THEN 1442560000 \
            ELSE 800000000 END)*100),2) as x_pencapaian \
            FROM \
            (SELECT \
            user_id as x_user_id, \
            SUM(amount_total) filter (WHERE  (state ='open' or state='paid') and type='out_invoice' and date_trunc('month', date_invoice) = date_trunc('month', current_date)) \
            AS x_total_omzet \
            FROM account_invoice \
            WHERE user_id=5 or user_id=7 or user_id=9 or user_id=31 or user_id=44 or user_id=56 or user_id=58 or user_id=59 or user_id=60 \
            GROUP BY x_user_id \
            )t \
            WINDOW window_bersih AS (PARTITION BY t.x_user_id) \
            ORDER BY x_pencapaian DESC"

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

def get_server_exception(tipe, nama):
    text=""
    if tipe=="ambil_data":
        resp=["Maaf {}. 🙏🏻 untuk saat ini Rin tidak bisa mengambil data dikarenakan ada gangguan koneksi ke server ",
              "Maaf {}. untuk saat ini tidak bisa memproses data. 🙏🏻",
              "{}. Terjadi gangguan disaat proses. silahkan coba lagi nanti",
              "Tidak bisa memproses data sekarang :(, silahkan dicoba lagi nanti {}.",
              "{}. Data tidak bisa diproses, masih ada kendala jaringan 🙏🏻"]
        random.shuffle(resp)
        text=resp[0].format(nama)
    return text
    
def get_manzada_user_id(tele_id):
    user_id = 1
    if tele_id=='3264582853639869':
        user_id=9
    if tele_id=='3941390309222663':
        user_id=31
    if tele_id=='3724789247576364':#'3706874686003580':
        user_id=7
    if tele_id=='4937492586295334': #Agung
        user_id=44
    if tele_id=='4345408962193459':
        user_id=25
    if tele_id=="3364431640310686":
        user_id=5
    if tele_id=="4294487443937631":
        user_id=56
    if tele_id=="25176516441947351":
        user_id=6
    if tele_id=="6281740698579175":
        user_id=58
    if tele_id=="6821994781252784":
        user_id=59
    return user_id

def is_int(s):
    result=False
    try:
        result=int(s)
    except ValueError:
        result = False
    return result

def reformat(s, n):
    n_spasi=0
    spasi = ''
    if len(s) < n:
        n_spasi=n-len(s)
        spasi = ' ' * n_spasi
    return s+spasi

def get_part_of_day(hour):
    return (
        "pagi" if 5 <= hour <= 11
        else
        "siang" if 12 <= hour <= 14
        else
        "sore" if 15 <= hour <= 17
        else
        "malam"
    )

# assume value is a decimal
def ribuan(value):
    str_value = str(value)+".00"
    separate_decimal = str_value.split(".")
    after_decimal = separate_decimal[0]
    before_decimal = separate_decimal[1]
    
    reverse = after_decimal[::-1]
    temp_reverse_value = ""
    
    for index, val in enumerate(reverse):
        if (index + 1) % 3 == 0 and index + 1 != len(reverse):
            temp_reverse_value = temp_reverse_value + val + "."
        else:
            temp_reverse_value = temp_reverse_value + val
            
    temp_result = temp_reverse_value[::-1]
    return temp_result + "," + before_decimal

def get_stat_server():
    text=""
    if check_server(SERVER, WEBPORT, TIMEOUT, RETRY):
        resp_check=["Server [Online] :)", "Server [Online]. Tidak ada masalah di sisi server\
        \nJika kesulitan membuka web\n1.Cek jaringan internet\n2.Kurangi beban memory HP\
        \n3.Bersihkan cache chrome\n4.Off\On Mode pesawat\n5.Restart HP"]
        random.shuffle(resp_check)
        text=resp_check[0]
    else:
        text="Maaf Bro. server sedang offline :("
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

def get_omzet(tele_id, nama):
    current_date = datetime.date.today()
    last_date=datetime.date(current_date.year + (current_date.month == 12), 
                            (current_date.month + 1 if current_date.month < 12 else 1), 1) - datetime.timedelta(1)
    begin_date=str(current_date.year)+' '+str(current_date.month)+' 01'
    end_date=str(current_date.year)+' '+str(current_date.month)+' '+str(last_date)
    text=""
    user_id=get_manzada_user_id(teleid_id)
    target_sales={
        5:3838464000,
        31:2632000000, #2050000000,
        7:2132480000, #1500000000,
        9:2531200000, #1500000000,
        44:1442560000, #1050000000,
        6:1288000000,
        56:2105600000,
        58:2132480000,
        59:1442560000}
    sales={
        5:"Zulkarnaen",
        31:"Ahmad Syarifudin",
        7:"Tedi Guntara",
        9:"Agus Ahmad Rian",
        44:"Agung Aprianto",
        56:"Adi",
        6:"Edi",
        58:"Bubun",
        59:"Fajar",
        60:"Dadang"}
    try:
        if check_server(SERVER, WEBPORT, TIMEOUT, RETRY):
            record=sql_query(sql_omzet)
            if record:
                total_omzet = 0
                grand_total = 0
                persentase = None
                rank=0
                for row in record:
                    crown=""
                    rank+=1
                    if rank == 1:
                        crown = "👑"
                    user_id=row[0]
                    if row[1]:
                        total_omzet=row[1]
                    else:
                        total_omzet=0
                    grand_total+=total_omzet
                    if row[2]:
                        persentase=row[2]
                    else:
                        persentase=0
                        #text = text + "\n\n" + sales[user_id] + " " + crown + "\n" + locale.format("%d",total_omzet,1) + "\t" + str(persentase) + "%"
                    text = text + "\n\n" + sales[user_id] + " " + crown + "\n" + ribuan(total_omzet) + "\t" + str(persentase) + "%"
                    print(text)
                #text=text + '\n\nGrand Total : ' + locale.format("%d", grand_total, 1)
                text=text + '\n\nGrand Total : ' + ribuan(grand_total)
            else:
                text="Maaf. Rin tidak bisa menemukan data omzet untuk saat ini."
        else:
            text=get_server_exception("ambil_data", "Bro")
    except Exception as e:
        text="Gagal memproses data, silahkan dicoba lagi.. {}".format(str(e))
    return text

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
    text = get_stat_server()
    await client.send_message(SENDER, text, parse_mode="HTML")

@client.on(events.NewMessage(pattern='/(?i)omzet')) 
async def time(event):
    # Get the sender of the message
    sender = await event.get_sender()
    SENDER = sender.id
    text = get_omzet(SENDER, "Bro")
    await client.send_message(SENDER, text, parse_mode="HTML")


### MAIN
if __name__ == '__main__':
    print("Bot Started!")
    client.run_until_disconnected()
