import time
import re
import random
import datetime
import telepot
from subprocess import call
import subprocess
import os
import sys
from telepot.loop import MessageLoop
import codecs
import psycopg2
import locale
import operator
import socket
from dateutil.relativedelta import relativedelta

locale.setlocale(locale.LC_ALL, '')

SERVER = "app.manzada.net"
WEBPORT = 80
TIMEOUT = 3
RETRY = 1
sql_draft = "SELECT \
            (SELECT name FROM res_partner WHERE id = ai.partner_id), \
            date_invoice, \
            amount_total \
            FROM \
            account_invoice ai \
            WHERE \
            state = 'draft' AND type = 'out_invoice' AND user_id = {}"
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
            WHEN x_user_id = 59 THEN 1442560000 \
            WHEN x_user_id = 60 THEN 1442560000 \
            ELSE 800000000 END)*100),2) as x_pencapaian \
            FROM \
            (SELECT \
            user_id as x_user_id, \
            SUM(amount_total) filter (WHERE  (state ='open' or state='paid') and type='out_invoice' and date_trunc('month', date_invoice) = date_trunc('month', current_date)) \
            AS x_total_omzet \
            FROM account_invoice \
            WHERE user_id=5 or user_id=7 or user_id=9 or user_id=31 or user_id=44 or user_id=59 or user_id=60 \
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
def get_draft(tele_id, nama):
    text=""
    user_id=get_manzada_user_id(tele_id)
    try:
        if check_server(SERVER, WEBPORT, TIMEOUT, RETRY):
            record=sql_query(sql_draft.format(9))
            if record:
                for row in record:
                    toko = row[0]
                    tgl = row[1]
                    amount_total = row[2]
                    grand_total+=amount_total
                    text=text+"""
{}
{}
Total : {}""".format(toko, str(tgl), locale.format("%d", amount_total, 1)) + '\n'
                text=text+"\nGrand Total : {}".format(locale.format("%d", grand_total, 1))
            else:
                text = "Tidak ada draft"
        else:
            text=get_server_exception("ambil_data", "Sob")
    except:
            text="Gagal memproses data, silahkan dicoba lagi.."
    return text
    
def get_omzet(tele_id, nama):
    current_date = datetime.date.today()
    last_date=datetime.date(current_date.year + (current_date.month == 12), 
                            (current_date.month + 1 if current_date.month < 12 else 1), 1) - datetime.timedelta(1)
    begin_date=str(current_date.year)+' '+str(current_date.month)+' 01'
    end_date=str(current_date.year)+' '+str(current_date.month)+' '+str(last_date)
    text=""
    user_id=get_manzada_user_id(tele_id)
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
                    text = text + "\n\n" + sales[user_id] + " " + crown + "\n" + ribuan(total_omzet) + "\t" + str(persentase) + "%"
                    print(text)
                text=text + '\n\nGrand Total : ' + ribuan(grand_total)
            else:
                text="Maaf. Rin tidak bisa menemukan data omzet untuk saat ini."
        else:
            text=get_server_exception("ambil_data", nama)
    except Exception as e:
        text="Gagal memproses data, silahkan dicoba lagi.. {}".format(str(e))
    return text
    
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
    if tele_id == 6729032463: #Agus
        user_id=9
    if tele_id=='3941390309222663':
        user_id=31
    if tele_id == 7355904419: #Tedi
        user_id=7
    if tele_id == 7215922306: #Agung
        user_id=44
    if tele_id=='4345408962193459':
        user_id=25
    if tele_id == 6169304151: #Zul
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

def getCommandHelp(line):
    if "#[" in line:
        start = line.find("#[") + len("]#")
        end = line.find("]#")
        return line[start:end]
    return ""


#Auto Commmand List
def search_string_in_file(file_name, string_to_search):
    """Search for the given string in file and return lines containing that string,
    along with line numbers"""
    list_of_results = []
    # Open the file in read only mode
    with open(file_name, 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            # For each line, check if line contains the string
            if string_to_search in line:
                if ("/?" not in line and not "o/" in line and not "," in line):
                    command = line
                    number = command.rfind("/")
                    command = command[number:]
                    number = command.rfind("'")
                    command = command[:number]
                    command = command + " " + getCommandHelp(line)  +"\n"
                    # If yes, then add the line number & line as a tuple in the list
                    list_of_results.append(command)
    # Return list of tuples containing line numbers and lines where string is found
    return list_of_results

def handle(msg):
    chat_id = msg['chat']['id']
    command = msg['text']
    
    if str(chat_id) not in os.getenv('ALLOWED_IDS'):
        bot.sendPhoto(chat_id,"https://github.com/t0mer/dockerbot/raw/master/No-Trespassing.gif")
        return ""
    if command == '__time': #* Get Local Time *#
        bot.sendMessage(chat_id, str(datetime.datetime.now()))
    elif command == '/getid': #[ Lihat ID telegram ]#
        bot.sendMessage(chat_id, str(chat_id))
    elif command == '/omzet': #[ Lihat Pencapaian Omzet ]#
        x = get_omzet(chat_id, "Sob")
        bot.sendMessage(chat_id,x)
    elif command == '__draft':
        x = get_draft(6729032463,"Sob")
        bot.sendMessage(chat_id,x)
    elif command == '__speed': #* Lihat Speed Starlink *#
        x = subprocess.check_output(['speedtest','--share'])
        urlb = re.search(br"(?P<url>http?://[^\s]+)", x).group("url")
        photo = codecs.decode(urlb, encoding='utf-8')
        bot.sendPhoto(chat_id,photo)
    elif command == '__ip': #* Get Real IP *#
        x = subprocess.check_output(['curl','ipinfo.io/ip'])
        bot.sendMessage(chat_id,x)
    elif command == '__disk': #* Info SSD Server *#
        x = subprocess.check_output(['df', '-h'])
        bot.sendMessage(chat_id,x)
    elif command == '__mem': #* Info Memory Server *#
        x = subprocess.check_output(['cat','/proc/meminfo'])
        bot.sendMessage(chat_id,x)
    elif command == '/stat': #[ Status BOT ]#
        bot.sendMessage(chat_id,'Rin Number five is alive!')
    elif command == '/?' or command=="/start":
        array = search_string_in_file('/opt/rin/rin.py', "/")
        s = "Command List:\n"
        for val in array:
            if ")" not in val:
                s+=str(val)
        x = s
        bot.sendMessage(chat_id,x)
    else:
        x = "Untuk melihat perintah yang bisa digunakan, silahkan ketik /start atau /?"
        bot.sendMessage(chat_id,x)

bot = telepot.Bot(os.getenv('API_KEY'))
MessageLoop(bot, handle).run_as_thread()
print('I am listening ...')
 
while 1:
    time.sleep(10)
