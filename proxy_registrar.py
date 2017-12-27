#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa user agent client
"""

import sys
import socket
import json
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
            json.dump(self.dicc, json_file, indent=3)

    def handle(self):
        self.json2register()
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if len(line) == 0:
                break
            receive = line.decode('utf-8').split()
            METHOD = receive[0]
            METHODS = 'REGISTER', 'INVITE', 'BYE'
            brline = line.decode('utf-8').split(' ')
            user = receive[1].split(':')[1]
            print(brline[1].split(':')[0])
            if ('sip:' not in brline[1] or brline[2] != 'SIP/2.0\r\n\r\n'):
                if METHOD in METHODS:
                    print(METHOD + ' recieved')
                    if METHOD == 'REGISTER':
                        if user in self.dicc:
                            self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                        else:
                            if len(receive) == 4:
                                self.wfile.write(b'SIP/2.0 401 Unauthorized\r\n')
                            elif len(receive) == 9:
                                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                                self.dicc[user] = (self.client_address[0],
                                                   self.client_address[1])
                    if METHOD == 'INVITE':
                        self.wfile.write(b'SIP/2.0 100 Trying\r\n\r\n')
                        self.wfile.write(b'SIP/2.0 180 Ringing\r\n\r\n')
                        self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                    elif METHOD == 'BYE':
                        self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                else:
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
    log = configtags[2][1]['path']

    serv = socketserver.UDPServer((proxy_ip, proxy_port), EchoHandler)
    print('Server ' + name + 'listening at port ' + str(proxy_port))
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print('servidor finalizado')
