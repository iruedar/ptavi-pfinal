#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa user agent client
"""

import os
import sys
import json
import time
import socket as skt
import socketserver
from hashlib import sha1
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from datetime import datetime, date, time, timedelta


def nonce(passwd, encoding='utf-8'):

    return sha1(passwd.encode(encoding)).hexdigest()


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
        msg = time_now + ' Error: ' + mnsg
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


class EchoHandler(socketserver.DatagramRequestHandler):

    dicc = {}

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

    def json2passwords(self):
        """Ver si registered.json existe."""
        try:
            with open(passwd, 'r') as json_file:
                self.dicc = json.load(json_file)
        except:
            pass

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
            print(receive)
            if METHOD in METHODS:
                print(METHOD + ' recieved')
                if METHOD == 'REGISTER':
                    sec = receive[3].split(':')[1]
                    port = receive[1].split(':')[2]
                    ip = self.client_address[0]
                    expires = datetime.now() + timedelta(seconds=int(sec))
                    date = expires.strftime(FORMAT)
                    now = datetime.now().strftime(FORMAT)
                    log_proxy.received_from(ip, port, mnsg)
                    try:
                        if int(sec) == 0:
                            del self.dicc[user]
                            self.wfile.write(b'SIP/2.0 200 OK0\r\n\r\n')
                        else:
                            if user in self.dicc:
                                self.dicc[user] = ('Ip:' +
                                                   self.client_address[0] +
                                                   ' Port:' + str(port) +
                                                   ' Registered from: ' + now +
                                                   ' Expires: ' + date)
                                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                                log_proxy.sent_to(ip, port, 'SIP/2.0 200 OK')
                            else:
                                if len(receive) == 4:
                                    Authen = 'SIP/2.0 401 Unauthorized\r\n'
                                    Authen += 'WWW Authenticate: Digest nonce='
                                    Authen += 'nonce\r\n\r\n'
                                    self.wfile.write(bytes(Authen, 'utf-8'))
                                    log_proxy.sent_to(ip, port, Authen)
                                elif len(receive) == 9:
                                    self.dicc[user] = ('Ip:' +
                                                       self.client_address[0] +
                                                       ' Port:' + str(port) +
                                                       ' Registered from: ' +
                                                       now + ' Expires: ' +
                                                       date)
                                    message = 'SIP/2.0 200 OK\r\n\r\n'
                                    self.wfile.write(bytes(message, 'utf-8'))
                                    log_proxy.sent_to(ip, port, message)
                    except KeyError:
                        message = 'SIP/2.0 404 User Not Found\r\n\r\n'
                        self.wfile.write(bytes(message, 'utf-8'))
                        log_proxy.sent_to(ip, port, message)
                elif METHOD == 'INVITE':
                    with skt.socket(skt.AF_INET, skt.SOCK_DGRAM) as sck:
                        try:
                            dst = receive[1].split(':')[1]
                            src = receive[6].split('=')[1]
                            src_ip = receive[7]
                            src_port = self.dicc.get(src).split()[1]
                            src_port = src_port.split(':')[1]
                            dst_ip = self.dicc.get(dst).split()[0]
                            dst_ip = dst_ip.split(':')[1].split()[0]
                            dst_port = self.dicc.get(dst).split()[1]
                            dst_port = dst_port.split(':')[1]
                            log_proxy.received_from(src_ip, src_port, mnsg)
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
                        except KeyError:
                            message = "SIP/2.0 404 User Not Found\r\n\r\n"
                            self.wfile.write(bytes(message, 'utf-8'))
                            log_proxy.sent_to(ip, port, message)
                        except ConnectionRefusedError:
                            error = 'No server listening at ' + dst_ip
                            error += ' port ' + str(dst_port)
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
                        print(LINE)
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
                        print(LINE)
                        Receive = msg.split(" ")
                        log_proxy.received_from(dst_ip, dst_port, msg)
                        self.wfile.write(data)
                        print(data.decode("utf-8"))
            elif METHOD not in METHOD:
                self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')
            else:
                self.wfile.write(b'SIP/2.0 400 Bad Request\r\n\r\n')
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
        sys.exit('File not found')
    except IndexError:
        sys.exit('Usage: ' + 'python3 uaserver.py config')

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
