import time
import re
import random
import calendar
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

#locale.setlocale(locale.LC_ALL, '')

SERVER = "app.manzada.net"
WEBPORT = 80
TIMEOUT = 3
RETRY = 1
global_err=""

sql_in = "SELECT (SELECT name FROM product_product where product_tmpl_id=sm.product_id) as nama, product_uos_qty, (select name from product_uom where id=sm.product_uom) from stock_move sm where date >= '{}' and origin like 'PO%' and sm.name not like 'ROKOK %' and state='done' order by nama asc"
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

sql_omzet_spec = "SELECT \
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
            SUM(amount_total) filter (WHERE  (state ='open' or state='paid') and type='out_invoice' and date_invoice >= '{}' and date_invoice <= '{}') \
            AS x_total_omzet \
            FROM account_invoice \
            WHERE user_id=5 or user_id=7 or user_id=9 or user_id=31 or user_id=44 or user_id=59 or user_id=60 \
            GROUP BY x_user_id \
            )t \
            WINDOW window_bersih AS (PARTITION BY t.x_user_id) \
            ORDER BY x_pencapaian DESC"

sql_insentif_salesman = "SELECT \
            concat(\
            (SELECT name FROM product_template WHERE name=t.x_name), \
            '(', x_komisi_produk::text, '/', x_target::text, ')') as x_nama_produk, \
            x_total_terjual,\
            round((CASE WHEN x_target >0 THEN \
            ((x_total_terjual/x_target)*100) \
            ELSE \
            0 \
            END),2) as x_persen_pencapaian,\
            (x_total_terjual * \
            CASE WHEN SUM(x_total_terjual) OVER (window_bersih) >= x_target * 0.8 THEN \
            x_komisi_produk \
            ELSE \
            0 \
            END) as x_insentif \
            FROM(\
            SELECT \
            name as x_name, \
            (SELECT user_id FROM account_invoice WHERE id=ail.invoice_id) as x_user_id,\
            (SELECT target_penjualan FROM product_template WHERE id = (select product_tmpl_id from product_product where id=ail.product_id)) as x_target,\
            (SELECT komisi_produk FROM product_template WHERE id = (select product_tmpl_id from product_product where id=ail.product_id)) as x_komisi_produk,\
            SUM(quantity) as x_total_terjual \
            FROM account_invoice_line ail \
            WHERE invoice_id IN (SELECT id FROM account_invoice WHERE state IN ('open', 'paid') \
            and type='out_invoice' \
            and user_id = {} and date_trunc('month', date_invoice) = date_trunc('month', current_date)) \
            AND name IN (SELECT name FROM product_template WHERE target_penjualan > 0) \
            AND uos_id IN (SELECT id FROM product_uom WHERE uom_type='reference') \
            GROUP BY x_user_id, x_name, ail.name, ail.product_id \
            )t \
            WINDOW window_bersih AS (PARTITION BY t.x_name, t.x_user_id)"

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
        #print(error)
        global_err=str(error)
        return False
    finally:
        if(conn_serv):
            cursor.close()
            conn_serv.close()
            return record
def get_draft(tele_id, nama):
    text=""
    date_format = '%Y-%m-%d' 
    user_id=get_manzada_user_id(tele_id)
    try:
        if check_server(SERVER, WEBPORT, TIMEOUT, RETRY):
            record=sql_query(sql_draft.format(user_id))
            if record:
                grand_total=0
                for row in record:
                    tgl = row[1]
                    if tgl:
                        if row[2] > 0:
                            tglobj = datetime.datetime.strptime(str(tgl), date_format)
                            tanggal = tglobj.strftime("%d-%m-%Y")
                            toko = row[0]
                            amount_total = row[2]
                            grand_total+=amount_total
                            text=text+"""
{}
{}
Total : {}""".format(toko, str(tanggal), ribuan(amount_total)) + '\n'
                text=text+"\nGrand Total : {}".format(ribuan(grand_total))
            else:
                text = "Tidak ada draft"
        else:
            text=get_server_exception("ambil_data", "Sob")
    except Exception as e:
        text = str(e)
        #text="Gagal memproses data, silahkan dicoba lagi.."
    return text
    
def get_omzet(tele_id, nama, bulan=None, tahun=None):
    x=None
    num_days=None
    tgl_awal=None
    tgl_akhir=None
    text=""
    textpre=""
    record=None
    if bulan and tahun:
        x,num_days=calendar.monthrange(int(tahun),int(bulan))
        x=None
        tgl_awal = tahun + "-" + bulan + "-01"
        tgl_akhir = tahun + "-" + bulan + "-" + str(num_days)
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
            if tgl_awal and tgl_akhir:
                record=sql_query(sql_omzet_spec.format(tgl_awal, tgl_akhir))
            else:
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
                    textpre=textpre+"""
{} {}
{}  {}""".format(sales[user_id],crown,ribuan(total_omzet)[:-3],str(persentase) + "%")
                    #text = text + "\n\n" + sales[user_id] + " " + crown + "\n" + ribuan(total_omzet) + "\t" + str(persentase) + "%"
                    #print(text)
                text="""
```
{}
----------------------------------
Grand Total : {}
```""".format(textpre,ribuan(grand_total)[:-3])
                #text=text + '\n\nGrand Total : ' + ribuan(grand_total)
            else:
                text="Maaf. Rin tidak bisa menemukan data omzet untuk saat ini."
        else:
            text=get_server_exception("ambil_data", nama)
    except Exception as e:
        text="Gagal memproses data, silahkan dicoba lagi.. {}".format(str(e))
    return text

def get_insentif(tele_id, nama, param=None):
    text=""
    textpre=""
    if check_server(SERVER, WEBPORT, TIMEOUT, RETRY):
        record=sql_query(sql_insentif_salesman.format(get_manzada_user_id(tele_id)))
        result=[]
        if record:
            produk = None
            terjual = 0
            persen = 0
            insentif = 0
            total_insentif = 0
            for row in record:
                produk=row[0]
                terjual=row[1]
                persen=row[2]
                insentif=row[3]
                total_insentif += insentif
                textpre=textpre+"""
{}
Terjual     : {}
Pencapaian  : {}%
Insentif    : {}""".format(produk, ribuan(terjual)[:-3], ribuan(persen)[:-3], ribuan(insentif)[:-3])
                #result.append(text)
                #text=""
            #if len(result) > 0:
            text="""
```
{}
------------------------------------------
Total Insentif Produk : {}
```""".format(textpre,ribuan(total_insentif)[:-3])
            #text=text+'\n------------------------------\n'
            #text=text+"Total Insentif Produk : " + ribuan(total_insentif)
        else:
            text="Maaf {}. Rin tidak bisa menemukan record insentif.".format(nama)
    else:
        text= get_server_exception("ambil_data", nama)
    return text
def get_product_in(nama,tanggal):
    textpre=""
    text=""
    if check_server(SERVER, WEBPORT, TIMEOUT, RETRY):
        record = sql_query(sql_in.format(tanggal))
        if record:
            produk = None
            qty = 0
            unit = None
            for row in record:
                produk = row[0]
                qty = row[1]
                unit = row[2]
                textpre=textpre+"{0:<30} {1} {2}".format(produk, ribuan(qty)[:-3], unit)+"\n"
            text="""
```
{}
```""".format(textpre)
        else:
            text = "Untuk saat ini belum ada pembelian"
    else:
        text = get_server_exception("ambil_data", nama)
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
    if tele_id == 7946838453: #Ahmad
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
    if tele_id == 7980569537: #Fajar
        user_id=59
    if tele_id == 7562971233: #Dadang
        user_id=60
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
    hmsg = msg['text']
    current_date = datetime.date.today()
    current_year = str(current_date.year)
    current_month = str(current_date.month)
    command = [""]
    tele_ids={
        6729032463:"Agus",
        7355904419:"Tedi",
        7215922306:"Agung",
        7980569537:"Fajar",
        7562971233:"Dadang",
        6169304151:"Zul",
        6299219117:"Me"}
    #7946838453:"Ahmad",
    #6169304151:"Zul",
    if hmsg:
        if hmsg.split():
            command = hmsg.split()
        z=tele_ids[chat_id]+" : "+hmsg
        bot.sendMessage(6299219117,z)
    if str(chat_id) not in os.getenv('ALLOWED_IDS'):
        bot.sendPhoto(chat_id,"https://github.com/t0mer/dockerbot/raw/master/No-Trespassing.gif")
        return ""
    if command[0] == '__time': #* Get Local Time *#
        bot.sendMessage(chat_id, str(datetime.datetime.now()))
    elif command[0] == '/getid': #[ Lihat ID telegram ]#
        bot.sendMessage(chat_id, str(chat_id))
    elif command[0] == '/omzet': #[ Lihat Pencapaian Omzet ]#
        x = get_omzet(chat_id, "Sob")
        if len(command)>1:
            x = "Jika ingin cek omzet periode tertentu, anda harus menulis bulan dalam format angka yang benar."
            if len(command) >= 2:
                bulan=command[1]
                tahun=current_year
                if bulan.isdigit():
                    passed=True
                    if int(tahun) == 2024:
                        if int(bulan) < 5:
                            x = "Pengecekan dibatasi, tidak bisa melewati dibawah bulan 5 2024"
                            passed=False
                    if int(bulan) < 1 or int(bulan) > 12:
                        x = "Format bulan salah. harus 1-12"
                        passed=False
                    if int(bulan) >= int(current_month) and int(bulan) < 13:
                        x = "Masa tidak boleh >= masa sekarang dan tahun berjalan, jika ingin cek pencapaian masa sekarang, ketik /omzet saja."
                        passed=False
                    if passed:
                        x = get_omzet(chat_id, "Sob", bulan, tahun)
        bot.sendMessage(chat_id,x,parse_mode="Markdown")
    elif command[0] == '/draft': #[ Lihat Draft Faktur ]#
        x = get_draft(chat_id,"Sob")
        bot.sendMessage(chat_id,x)
    elif command[0] == '/inp': #[ Lihat Insentif Produk ]#
        x = get_insentif(chat_id,"Sob")
        bot.sendMessage(chat_id,x,parse_mode="Markdown")
    elif command[0] == '__inp': #* Lihat Insentif Produk *#
        x = get_insentif(6729032463,"Sob")
        bot.sendMessage(chat_id,x,parse_mode="Markdown")
    elif command[0] == '/in': #[ Info Barang Masuk ]#
        x = get_product_in("Sob",str(current_date))
        if x:
            bot.sendMessage(chat_id,x,parse_mode="Markdown")
        else:
            bot.sendMessage(6299219117,global_err)
    elif command[0] == '__draft':
        x = get_draft(6729032463,"Sob")
        bot.sendMessage(chat_id,x)
    elif command[0] == '__speed': #* Lihat Speed Starlink *#
        x = subprocess.check_output(['speedtest','--share'])
        urlb = re.search(br"(?P<url>http?://[^\s]+)", x).group("url")
        photo = codecs.decode(urlb, encoding='utf-8')
        bot.sendPhoto(chat_id,photo)
    elif command[0] == '__ip': #* Get Real IP *#
        x = subprocess.check_output(['curl','ipinfo.io/ip'])
        bot.sendMessage(chat_id,x)
    elif command[0] == '__disk': #* Info SSD Server *#
        x = subprocess.check_output(['df', '-h'])
        bot.sendMessage(chat_id,x)
    elif command[0] == '__mem': #* Info Memory Server *#
        x = subprocess.check_output(['cat','/proc/meminfo'])
        bot.sendMessage(chat_id,x)
    elif command[0] == '/stat': #[ Status BOT ]#
        bot.sendMessage(chat_id,'Rin Number five is alive!')
    elif command[0] == '/?' or command[0]=="/start":
        array = search_string_in_file('/opt/rin/rin.py', "/")
        s = "Command List:\n"
        for val in array:
            if ")" not in val:
                s+=str(val)
        x = s
        bot.sendMessage(chat_id,x)
    elif command[0] == '__all':
        if len(command) > 1:
            try:
                x=""
                for r in command:
                    if r != "__all":
                        x=x+r+" "
                for k, v in tele_ids.items():
                    bot.sendMessage(k,x)
            except Exception as e:
                bot.sendMessage(chat_id, str(e))
    else:
        x = "Untuk melihat perintah yang bisa digunakan, silahkan ketik /start atau /?"
        bot.sendMessage(chat_id,x)

bot = telepot.Bot(os.getenv('API_KEY'))
MessageLoop(bot, handle).run_as_thread()
print('I am listening ...')
 
while 1:
    time.sleep(10)
