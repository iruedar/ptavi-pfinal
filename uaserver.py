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

USAGE = 'python3 uaserver.py config'

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
            'regproxy' : ['ip', 'puerto'],
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
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if len(line) == 0:
                break

            receive = line.decode('utf-8').split()
            METHOD = receive[0]
            METHODS = 'REGISTER', 'INVITE', 'ACK', 'BYE'
            RTP = './mp32rtp -i 127.0.0.1 -p 23032 < ' + 'FILE'
            brline = line.decode('utf-8').split(' ')
            if METHOD in METHODS:
                print(METHOD + ' recieved')
                if METHOD == 'INVITE':
                    print('enviamos invite')
                    self.wfile.write(b'SIP/2.0 100 Trying\r\n\r\n')
                    self.wfile.write(b'SIP/2.0 180 Ringing\r\n\r\n')
                    self.wfile.write(b'SIP/2.0 200 OK\r\n')
                    LINE = "Content-Type: application/sdp\r\n\r\n"
                    LINE += "v=0\r\no=" + username + " " + uaserv_ip
                    LINE += "\r\ns=sesion" + "\r\nt=0\r\nm=audio "
                    LINE += audio_port + " RTP"
                    SDP = (bytes(LINE, "utf-8"))
                    self.wfile.write(SDP)
                elif METHOD == 'BYE':
                    self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
            elif METHOD not in METHOD:
                self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')
            else:
                self.wfile.write(b'SIP/2.0 400 Bad Request\r\n\r\n')

if __name__ == "__main__":
    parser = make_parser()
    Handler = XMLHandler()
    parser.setContentHandler(Handler)
    parser.parse(open(CONFIG))
    print(Handler.get_tags())
    configtags = Handler.get_tags()
    
    username = configtags[0][1]['username']
    passwd = configtags[0][1]['passwd']
    uaserv_ip = configtags[1][1]['ip']
    uaserv_port = int(configtags[1][1]['puerto'])
    audio_port = (configtags[2][1]['puerto'])
    proxy_ip = configtags[3][1]['ip']
    proxy_port = int(configtags[3][1]['puerto'])
    log = configtags[4][1]['path']
    audio = configtags[5][1]['path']

    serv = socketserver.UDPServer((uaserv_ip, uaserv_port), EchoHandler)
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print('servidor finalizado')
