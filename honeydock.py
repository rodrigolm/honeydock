# -*- coding: utf-8 -*-

import pyinotify
import re
import subprocess
import time
import logging
from logging.handlers import RotatingFileHandler
import MySQLdb
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# Global Variables

HONEYPOT_SERVICES_PORTS = ["22"]
CONN_LOG_FILE_PATH = "/var/log/kern.log"
CONN_LOG_CONTENT = open(CONN_LOG_FILE_PATH, 'r').readlines()
CONN_LOG_LEN = len(CONN_LOG_CONTENT)
INTERFACE = "eth0"

# Pyinotify

wm = pyinotify.WatchManager()
mask = pyinotify.IN_MODIFY

# Open database connection
CONN_DB = MySQLdb.connect("localhost",user,password,db)
CONN = CONN_DB.cursor()

def banner():
    subprocess.Popen(["clear"], stdout=subprocess.PIPE, shell=True)
    print ""
    print "   _                                _            _     "
    print "  | |                              | |          | |    "
    print "  | |__   ___  _ __   ___ _   _  __| | ___   ___| | __ "
    print "  | '_ \ / _ \| '_ \ / _ \ | | |/ _` |/ _ \ / __| |/ / "
    print "  | | | | (_) | | | |  __/ |_| | (_| | (_) | (__|   <  "
    print "  |_| |_|\___/|_| |_|\___|\__, |\__,_|\___/ \___|_|\_\ "
    print "                           __/ |                       "
    print "                          |___/                   v0.1 "
    print ""

def send_email_alert(attacker_ip, option):
    fromaddr = ''
    toaddr = ''
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "HoneyDock Attack Alert"

    if option == 1:
        body = "HoneyDock just received a new connection from: " + attacker_ip
    else:
        body = "HoneyDock just received another connection from: " + attacker_ip

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('', 587)
    server.starttls()
    server.login('', '')
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def get_local_ip():
    local_ip = subprocess.Popen(["ifconfig | grep -A 1 {interface} | grep -Eo 'inet (addr:)?([0-9]*\.){{3}}[0-9]*' | grep -Eo '([0-9]*\.){{3}}[0-9]*' | grep -v '127.0.0.1'".format(interface=INTERFACE)], stdout=subprocess.PIPE, shell=True)
    (out, err) = local_ip.communicate()
    return out.strip()

def check_attacker(ip):
    CONN.execute("SELECT * FROM attacker WHERE ip='{attacker_ip}'".format(attacker_ip=ip))
    all_rows = CONN.fetchall()
    return len(all_rows)

def add_attacker(ip):
    try:
        CONN.execute("INSERT INTO attacker (ip) VALUES ('{attacker_ip}')".format(attacker_ip=ip))
        CONN_DB.commit()
    except:
        CONN_DB.rollback()

def create_container(src_port, dst_port, image_name):
    docker_run = subprocess.Popen(["docker run -d -p {src}:{dst} {image}".format(src=src_port, dst=dst_port, image=image_name)], stdout=subprocess.PIPE, shell=True)
    (out, err) = docker_run.communicate()
    container_id = out[:12]
    add_container(container_id, int(src_port), 1)

def add_container(container_id, port, availability):
    CONN.execute("INSERT INTO container (container_id, port, available) VALUES ('{id}', {port}, {available})".format(id=container_id, port=port, available=availability))
    CONN_DB.commit()

#def attach_to_container(attacker_ip, container_port):

def available_container():
    CONN.execute("SELECT port FROM container WHERE available=1")
    port = CONN.fetchone()
    if port:
        return str(port[0])
    else:
        port = str(available_port())
        create_container(port, str(22), "honeypot-ssh")
        return port

def available_port():
    CONN.execute("SELECT port FROM container")
    result = CONN.fetchall()
    for i in range(22222, 65536):
        if [port for port in result if port[0] == i]:
            pass
        else:
            return i

def set_unavailable_port(port):
    CONN.execute("UPDATE container SET available = 0 WHERE port = {port}".format(port=port))

class EventHandler (pyinotify.ProcessEvent):

    def __init__(self, file_path, *args, **kwargs):
        super(EventHandler, self).__init__(*args, **kwargs)
        self.file_path = file_path
        self._last_position = 0
        logpats = r'I2G\(JV\)'
        self._logpat = re.compile(logpats)

    def process_IN_MODIFY(self, event):
        global CONN_LOG_CONTENT
        global CONN_LOG_LEN

        # print "[INFO] Log file changed: ", event.pathname

        loglines = open(self.file_path, 'r').readlines()
        loglines_len = len(loglines)
        diff = loglines_len - CONN_LOG_LEN
        changes = loglines[-diff:]
        
        CONN_LOG_CONTENT = open(CONN_LOG_FILE_PATH, 'r').readlines()
        CONN_LOG_LEN = len(CONN_LOG_CONTENT)

        for s in changes:
            if "Connection established:" in s:
                DST = (re.search(r'DST=(.*?) ', s)).group(1)
                SPT = (re.search(r'SPT=(.*?) ', s)).group(1)

                attacker_ip = DST
                logger.debug("New connection was established!")
                logger.debug("Connection detail: {}".format(s))

                logger.warn("Attacker ({}) on SSH service!".format(DST))
                num_attacker = check_attacker(DST)
                if num_attacker == 0:
                    logger.info("The IP: {} it's from a new attacker.".format(DST))
                    send_email_alert(attacker_ip, 1)
                    logger.info("E-mail alert sent.")
                    add_attacker(DST)                            
                    logger.info("The IP: {} was added on attacker's table.".format(DST))

                    logger.debug("Getting an available docker.")
                    port = available_container()

                    logger.info("Attaching this IP to a docker instance")
                    # [PENDENTE] IPTABLES AQUI
                    set_unavailable_port(port)

                    logger.info("Creating a new docker instance")
                    next_port = available_port()
                    # CRIAR O DOCKER EM UMA NOVA PORTA
                    create_container(next_port, "22", "honeypot-ssh")
                            
                    logger.info("New docker container created on port {port}".format(port=next_port))
                    # [PENDENTE] ADICIONA O NOVO DOCKER AO BANCO DE DADOS
                    # QUALQUER OUTRO IP DEVE SER DIRECIONADO A ESSE NOVO DOCKER
                else:
                    logger.info("The IP: {} it's  from a returning attacker. No action required".format(DST))
                    send_email_alert(attacker_ip, 2)
                    #CONN_DB.commit()

                    # checa se o attacker ip ja existe no banco
                    # se existir, nao faz nada
                    # se nao existir, adiciona o ip ao banco

logger = logging.getLogger(__name__)
logging.root.handlers = []
logging.basicConfig(format="[%(asctime)s] [%(threadName)s] [%(levelname)s]: %(message)s", level=logging.DEBUG , filename="honeydock.log")

# Create a console handler
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)

# Create a logging format
formatter = logging.Formatter("[%(asctime)s] [%(threadName)s] [%(levelname)s]: %(message)s")
console.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console)

banner()

logger.info("Initializing...")
logger.info("Starting base docker." )

docker_run = subprocess.Popen(["docker run -d -p 22222:22 honeypot-ssh"], stdout=subprocess.PIPE, shell=True)
(out, err) = docker_run.communicate()
container_id = out[:12]
add_container(container_id, 22222, 1)

logger.info("SSH base docker has started.")
logger.info("Creating initial iptables rules...")
# LEMBRAR DE DEIXAR ESSE IP DA MAQUINA DINAMICO/CONFIGURAVEL
subprocess.Popen(["iptables -t nat -A PREROUTING -p tcp -d {local_ip} --dport 22 -j DNAT --to {local_ip}:22222".format(local_ip=get_local_ip())], stdout=subprocess.PIPE, shell=True)
# LEMBRAR DE DEIXAR A INTERFACE DA MAQUINA DINAMICA/CONFIGURAVEL (ens33)
subprocess.Popen(["iptables -A INPUT -i {interface} -p tcp --dport 22 -m state --state NEW,ESTABLISHED -j ACCEPT".format(interface=INTERFACE)], stdout=subprocess.PIPE, shell=True)
subprocess.Popen(["iptables -A OUTPUT -o {interface} -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT".format(interface=INTERFACE)], stdout=subprocess.PIPE, shell=True)
subprocess.Popen(["iptables -A OUTPUT -p tcp --tcp-flags SYN,ACK SYN,ACK -j LOG --log-prefix \"Connection established: \" "], stdout=subprocess.PIPE, shell=True)

logger.info("Rules created. Honeydock is ready to go. :)")

handler = EventHandler(CONN_LOG_FILE_PATH)
notifier = pyinotify.Notifier(wm, handler)

wm.add_watch(handler.file_path, mask)        
notifier.loop()

