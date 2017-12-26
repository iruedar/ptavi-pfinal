#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa user agent client
"""

import sys
import socket
import socketserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

USAGE = 'python3 uaclient.py config'

try:
    CONFIG = sys.argv[1]
except IndexError:
    sys.exit('Usage: ' + USAGE)

class XMLHandler(ContentHandler):

    def __init__(self):     #Declaramos las listas de los elementos
        self.list_element = []
        self.element = {
            'account' : ['username', 'passwd'],
            'uaserver' : ['ip', 'puerto'],
            'rtpaudio' : ['puerto'],
            'regproxy' : ['ip','puerto'],
            'log' : ['path'],
            'audio' : ['path']}

    def startElement(self, name, element):      #Añade elementos
        dicc = {}
        if name in self.element:
            for elment in self.element[name]:
                dicc[elment] = element.get(elment, '')
            self.list_element.append([name, dicc])

    def get_tags(self):      #Devuelve la lista con elementos encontrados
        return self.list_element

class EchoHandler(socketserver.DatagramRequestHandler):

    def handle(self):
         for line in self.rfile:
            if len(line) == 0:
                break

            METHOD = line.decode('utf-8').split(' ')[0]
            METHODS = 'INVITE', 'ACK', 'BYE'
            RTP = './mp32rtp -i 127.0.0.1 -p 23032 < ' + FILE
            brline = line.decode('utf-8').split(' ')
            if ('sip:' not in brline[1] or '@' not in brline[1] or
               brline[2] != 'SIP/2.0\r\n\r\n'):
                self.wfile.write(b'SIP/2.0 Bad Request\r\n\r\n')
            else:
                if METHOD in METHODS:
                    print(METHOD + ' recieved')
                    if METHOD == 'REGISTER':
                        self.wwile.write(b'SIP/2.0 401 Unauthorized\r\n\r\n')
                    if METHOD == 'INVITE':
                        self.wfile.write(b'SIP/2.0 100 Trying\r\n\r\n')
                        self.wfile.write(b'SIP/2.0 180 Ringing\r\n\r\n')
                        self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                    elif METHOD == 'BYE':
                        self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                    elif METHOD == 'ACK':
                        print('Ejecutamos ' + FILE)
                        os.system(RTP)
                else:
                    self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')

if __name__ == "__main__":
    parser = make_parser()
    Handler = XMLHandler()
    parser.setContentHandler(Handler)
    parser.parse(open(CONFIG))
    print(Handler.get_tags())
