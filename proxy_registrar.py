#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa user agent client
"""

import os
import sys
import json
import time
import random
import hashlib
import socketserver
import socket as skt
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from datetime import datetime, date, time, timedelta


class XMLHandler(ContentHandler):

    def __init__(self):
        self.list_element = []
        self.element = {
            'server': ['name', 'ip', 'puerto'],
            'database': ['path', 'passwdpath'],
            'log': ['path']}

    def startElement(self, name, element):
        dicc = {}
        if name in self.element:
            for elment in self.element[name]:
                dicc[elment] = element.get(elment, '')
            self.list_element.append([name, dicc])

    def get_tags(self):
        return self.list_element


class Log():

    def __init__(self, file_log):
        if not os.path.exists(file_log):
            os.system('touch ' + file_log)
        self.log = file_log

    def write_log(self, msg):
        log_write = open(self.log, 'a')
        log_write.write(msg)
        log_write.close()

    def time(self):
        FORMAT = '%Y%m%d%H%M%S'
        now = datetime.now().strftime(FORMAT)
        return(now)

    def sent_to(self, ip, port, mnsg):
        time_now = self.time()
        msg = time_now + ' Send to ' + ip + ':' + str(port) + ': '
        msg += mnsg.replace('\r\n', ' ') + '\r\n'
        self.write_log(msg)

    def received_from(self, ip, port, mnsg):
        time_now = self.time()
        msg = time_now + ' Received from ' + ip + ':' + str(port) + ': '
        msg += mnsg.replace('\r\n', ' ') + '\r\n'
        self.write_log(msg)

    def error(self, mnsg):
        time_now = self.time()
        msg = time_now + ' Error: '
        msg += mnsg.replace('\r\n', ' ') + '\r\n'
        self.write_log(msg)
    
    def ejecutando(self, ip, port, mnsg):
        time_now = self.time()
        msg = time_now + ' Ejecutando canción ' + ip + ':' + str(port) + ': '
        msg += mnsg.replace('\r\n', ' ') + '\r\n'
        self.write_log(msg)

    def start(self):
        time_now = self.time()
        msg = time_now + ' Starting...\n'
        self.write_log(msg)

    def finish(self):
        time_now = self.time()
        msg = time_now + ' Finishing.\n'
        self.write_log(msg)

def passwords(user):
    with open(passwd, 'r') as passwd_file:
        for line in passwd_file:
            user_file = line.split()[0]
            if user == user_file:
                password = line.split()[2].split('=')[1]
        return password

def checknonce(nonce, user):
    fun_check = hashlib.md5()
    fun_check.update(bytes(nonce, 'utf-8'))
    fun_check.update(bytes(passwords(user), 'utf-8'))
    fun_check.digest()
    return fun_check.hexdigest()


class EchoHandler(socketserver.DatagramRequestHandler):

    dicc = {}
    nonce = {}

    def json2register(self):
        """Ver si registered.json existe."""
        try:
            with open(database, 'r') as json_file:
                self.dicc = json.load(json_file)
        except:
            pass

    def register2json(self):
        """Crea registered.json file."""
        with open(database, 'w') as json_file:
            json.dump(self.dicc, json_file, indent=2)
            
    def delete(self):

        delete_list = []
        FORMAT = '%Y-%m-%d %H:%M:%S'
        for client in self.dicc:
            self.expire = self.dicc[client][-1]
            now = datetime.now().strftime(FORMAT)
            if self.expire < now:
                delete_list.append(client)
        for cliente in delete_list:
            del self.dicc[cliente]
        self.register2json()

    def handle(self):
        self.json2register()
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if len(line) == 0:
                break
            mnsg = line.decode('utf-8')
            receive = mnsg.split()
            METHOD = receive[0]
            METHODS = 'REGISTER', 'INVITE', 'BYE', 'ACK'
            user = receive[1].split(':')[1]
            FORMAT = '%Y-%m-%d %H:%M:%S'
            nonce = str(random.randint(00000000,99999999))
            print(receive)
            if METHOD in METHODS:
                print(METHOD + ' recieved')
                if METHOD == 'REGISTER':
                    sec = receive[3].split(':')[1]
                    port = str(receive[1].split(':')[2])
                    ip = self.client_address[0]
                    expires = datetime.now() + timedelta(seconds=int(sec))
                    date = expires.strftime(FORMAT)
                    now = datetime.now().strftime(FORMAT)
                    log_proxy.received_from(ip, port, mnsg)
                    try:
                        if int(sec) == 0:
                            del self.dicc[user]
                            self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                        else:
                            if user in self.dicc:
                                self.dicc[user] = ('Ip:' + ip +
                                                   ' Port:' + port +
                                                   ' Registered: ' + now +
                                                   ' Expires: ' + date)
                                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                                log_proxy.sent_to(ip, port, 'SIP/2.0 200 OK')
                            else:
                                if len(receive) == 4:
                                    self.nonce[user] = nonce
                                    Authen = 'SIP/2.0 401 Unauthorized\r\n'
                                    Authen += 'WWW Authenticate: Digest nonce='
                                    Authen += self.nonce[user] + '\r\n\r\n'
                                    self.wfile.write(bytes(Authen, 'utf-8'))
                                    log_proxy.sent_to(ip, port, Authen)
                                elif len(receive) == 9:
                                    client_response = receive[-1]
                                    respse = checknonce(self.nonce[user], user)
                                    if client_response == respse:
                                        self.dicc[user] = ('Ip:' + ip +
                                                           ' Port:' + port +
                                                           ' Registered: ' +
                                                           now + ' Expires: ' +
                                                           date)
                                        msg = 'SIP/2.0 200 OK\r\n\r\n'
                                        self.wfile.write(bytes(msg, 'utf-8'))
                                        log_proxy.sent_to(ip, port, msg)
                                    else:
                                        error = 'Contraseña incorrecta'
                                        print(error)
                                        log_proxy.erro(error)
                    except KeyError:
                        message = 'SIP/2.0 404 User Not Found\r\n\r\n'
                        self.wfile.write(bytes(message, 'utf-8'))
                        log_proxy.sent_to(ip, port, message)
                elif METHOD == 'INVITE':
                    try:
                        with skt.socket(skt.AF_INET, skt.SOCK_DGRAM) as sck:
                            src = receive[6].split('=')[1]
                            src_ip = receive[7]
                            src_port = self.dicc.get(src).split()[1]
                            src_port = src_port.split(':')[1]
                            log_proxy.received_from(src_ip, src_port, mnsg)
                            if user in self.dicc:
                                dst = receive[1].split(':')[1]
                                dst_ip = self.dicc.get(dst).split()[0]
                                dst_ip = dst_ip.split(':')[1].split()[0]
                                dst_port = self.dicc.get(dst).split()[1]
                                dst_port = dst_port.split(':')[1]
                                sck.connect((dst_ip, int(dst_port)))
                                sck.send(bytes(mnsg, 'utf-8'))
                                log_proxy.sent_to(dst_ip, dst_port, mnsg)
                                print(mnsg)
                                data = sck.recv(1024)
                                msg = data.decode("utf-8")
                                print(msg)
                                Receive = msg.split(" ")
                                log_proxy.received_from(dst_ip, dst_port, msg)
                                if Receive[1] == "100":
                                    self.wfile.write(data)
                                    log_proxy.sent_to(src_ip, src_port, msg)
                            else:
                                message = "SIP/2.0 404 User Not Found\r\n\r\n"
                                self.wfile.write(bytes(message, 'utf-8'))
                                log_proxy.sent_to(src_ip, src_port, message)
                    except ConnectionRefusedError:
                        error = "No server listening "
                        log_proxy.error(error)
                        sys.exit(error)
                elif METHOD == 'ACK':
                    with skt.socket(skt.AF_INET, skt.SOCK_DGRAM) as my_socket:
                        src_ip = self.client_address[0]
                        src_port = self.client_address[1]
                        dst = receive[1].split(':')[1]
                        dst_ip = self.dicc.get(dst).split()[0]
                        dst_ip = dst_ip.split(':')[1].split()[0]
                        dst_port = self.dicc.get(dst).split()[1].split(':')[1]
                        log_proxy.received_from(src_ip, src_port, mnsg)
                        my_socket.connect((dst_ip, int(dst_port)))
                        my_socket.send(bytes(mnsg, 'utf-8'))
                        log_proxy.sent_to(dst_ip, dst_port, mnsg)
                        print(mnsg)
                elif METHOD == 'BYE':
                    with skt.socket(skt.AF_INET, skt.SOCK_DGRAM) as my_socket:
                        src_ip = self.client_address[0]
                        src_port = self.client_address[1]
                        dst = receive[1].split(':')[1]
                        dst_ip = self.dicc.get(dst).split()[0]
                        dst_ip = dst_ip.split(':')[1].split()[0]
                        dst_port = self.dicc.get(dst).split()[1].split(':')[1]
                        log_proxy.received_from(src_ip, src_port, mnsg)
                        my_socket.connect((dst_ip, int(dst_port)))
                        my_socket.send(bytes(mnsg, 'utf-8'))
                        log_proxy.sent_to(dst_ip, dst_port, mnsg)
                        data = my_socket.recv(1024)
                        msg = data.decode('utf-8')
                        print(mnsg)
                        Receive = msg.split(" ")
                        log_proxy.received_from(dst_ip, dst_port, msg)
                        self.wfile.write(data)
                        log_proxy.sent_to(src_ip, src_port, msg)
                        print(data.decode("utf-8"))
            elif METHOD not in METHOD:
                error = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(bytes(error, 'utf-8'))
            else:
                error = 'SIP/2.0 400 Bad Request\r\n\r\n'
                self.wfile.write(bytes(error, 'utf-8'))
            self.delete()
            self.register2json()

if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
        parser = make_parser()
        Handler = XMLHandler()
        parser.setContentHandler(Handler)
        parser.parse(open(CONFIG))
        print(Handler.get_tags())
        configtags = Handler.get_tags()
    except FileNotFoundError:
        error = 'File not found'
        sys.exit(error)
        log_proxy.error(error)
    except IndexError:
        error = 'Usage: python3 uaserver.py config'
        sys.exit(error)
        log_proxy.error(error)

    name = configtags[0][1]['name']
    proxy_ip = configtags[0][1]['ip']
    proxy_port = int(configtags[0][1]['puerto'])
    database = configtags[1][1]['path']
    passwd = configtags[1][1]['passwdpath']
    file_log = configtags[2][1]['path']
    log_proxy = Log(file_log)

    serv = socketserver.UDPServer((proxy_ip, proxy_port), EchoHandler)
    log_proxy.start()

    print('Server ' + name + ' listening at port ' + str(proxy_port))
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log_proxy.finish()
        print('servidor finalizado')
