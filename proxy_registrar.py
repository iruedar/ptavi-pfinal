#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa user agent client
"""

import os
import sys
import json
import time
import socket
import socketserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from datetime import datetime, date, time, timedelta

USAGE = 'python3 uaserver.py config'

try:
    CONFIG = sys.argv[1]
except IndexError:
    sys.exit('Usage: ' + USAGE)

class XMLHandler(ContentHandler):

    def __init__(self):     #Declaramos las listas de los elementos
        self.list_element = []
        self.element = {
            'server' : ['name', 'ip', 'puerto'],
            'database' : ['path', 'passwdpath'],
            'log' : ['path']}

    def startElement(self, name, element):      #Añade elementos
        dicc = {}
        if name in self.element:
            for elment in self.element[name]:
                dicc[elment] = element.get(elment, '')
            self.list_element.append([name, dicc])

    def get_tags(self):      #Devuelve la lista con elementos encontrados
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
            with open('registered.json', 'r') as json_file:
                self.dicc = json.load(json_file)
        except:
            pass

    def register2json(self):
        """Crea registered.json file."""
        with open('registered.json', 'w') as json_file:
            json.dump(self.dicc, json_file, indent=2)

    def handle(self):
        self.json2register()
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if len(line) == 0:
                break
            receive = line.decode('utf-8').split()
            METHOD = receive[0]
            METHODS = 'REGISTER', 'INVITE', 'BYE', 'ACK'
            user = receive[1].split(':')[1]
            FORMAT = '%Y-%m-%d %H:%M:%S'
            print(receive)
            if METHOD in METHODS:
                print(METHOD + ' recieved')
                if METHOD == 'REGISTER':
                    sec = receive[3].split(':')[1]
                    port = receive[1].split(":")[2]
                    expires = datetime.now() + timedelta(seconds=int(sec))
                    date = expires.strftime(FORMAT)
                    now = datetime.now().strftime(FORMAT)
                    if user in self.dicc:
                        self.dicc[user] = ('Ip:' + self.client_address[0] + 
                                           ' Port:' + str(port) + 
                                           ' Registerd from: ' + now +
                                           ' Expires: ' + date)
                        self.wfile.write(b'SIP/2.0 200 OK0\r\n\r\n')
                    else:
                        if len(receive) == 4:
                            self.wfile.write(b"SIP/2.0 401 Unauthorized\r\n")
                            self.wfile.write(b"WWW Authenticate:" +
                                             b"Digest nonce=" + nonce)
                            self.wfile.write(b"\r\n\r\n")
                        elif len(receive) == 9:
                            self.dicc[user] = ('Ip:' + self.client_address[0] + 
                                               ' Port:' + str(port) + 
                                               ' Registerd from: ' + now +
                                               ' Expires: ' + date)
                            self.wfile.write(b'SIP/2.0 200 OKa\r\n\r\n')
                elif METHOD == 'INVITE':
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
                        dst = receive[1].split(':')[1]
                        src = receive[6].split('=')[1]
                        src_ip = receive[7]
                        src_port = self.dicc.get(src).split()[1].split(':')[1]
                        dst_ip = self.dicc.get(dst).split()[0].split(':')[1].split()[0]
                        dst_port = self.dicc.get(dst).split()[1].split(':')[1]
                        aud_port = receive[11]
                        my_socket.connect((dst_ip, int(dst_port)))
                        LINE = "INVITE sip:" + dst + " SIP/2.0\r\n"
                        LINE += "Content-Type: application/sdp\r\n\r\n"
                        LINE += "v=0\r\no=" + src + " " + src_ip
                        LINE += "\r\ns=sesion" + "\r\nt=0\r\nm=audio "
                        LINE += aud_port + " RTP"
                        my_socket.send(bytes(LINE, "utf-8"))
                        print(LINE)
                        data = my_socket.recv(1024)
                        print(data.decode("utf-8"))

                        Receive = data.decode('utf-8').split(" ")
                        if Receive[1] ==  "100":
                            self.wfile.write(data)
                elif METHOD == 'ACK':
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
                        dst = receive[1].split(':')[1]
                        dst_ip = self.dicc.get(dst).split()[0].split(':')[1].split()[0]
                        dst_port = self.dicc.get(dst).split()[1].split(':')[1]
                        my_socket.connect((dst_ip, int(dst_port)))
                        LINE = 'ACK' + ' sip:' + dst + ' SIP/2.0\r\n\r\n'
                        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
                        data = my_socket.recv(1024)
                        print(LINE)
                elif METHOD == 'BYE':
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
                        dst = receive[1].split(':')[1]
                        dst_ip = self.dicc.get(dst).split()[0].split(':')[1].split()[0]
                        dst_port = self.dicc.get(dst).split()[1].split(':')[1]
                        my_socket.connect((dst_ip, int(dst_port)))
                        LINE = 'BYE' + ' sip:' + dst + ' SIP/2.0\r\n\r\n'
                        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
                        data = my_socket.recv(1024)
                        print(LINE)
                        Receive = data.decode('utf-8').split(" ")
                        self.wfile.write(data)
                        print(data.decode("utf-8"))
            elif METHOD not in METHOD:
                self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')
            else:
                self.wfile.write(b'SIP/2.0 400 Bad Request\r\n\r\n')
            self.register2json()

if __name__ == "__main__":
    parser = make_parser()
    Handler = XMLHandler()
    parser.setContentHandler(Handler)
    parser.parse(open(CONFIG))
    print(Handler.get_tags())
    configtags = Handler.get_tags()
    
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
