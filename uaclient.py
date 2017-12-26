#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa user agent client
"""

import sys
import socket
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

USAGE = 'python3 uaclient.py config method option'

try:
    METHOD = str.upper(sys.argv[2])
    CONFIG = sys.argv[1]
    OPTION = sys.argv[3]
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

if __name__ == "__main__":
    parser = make_parser()
    Handler = XMLHandler()
    parser.setContentHandler(Handler)
    parser.parse(open(CONFIG))
    configtags = Handler.get_tags()

    username = configtags[0][1]['username']
    passwd = configtags[0][1]['passwd']
    uaserv_ip = configtags[1][1]['ip']
    uaserv_port = str(configtags[1][1]['puerto'])
    audio_port = int(configtags[1][1]['puerto'])
    proxy_ip = configtags[3][1]['ip']
    proxy_port = int(configtags[3][1]['puerto'])
    log = configtags[4][1]['path']
    audio = configtags[5][1]['path']

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((proxy_ip, proxy_port))

    if METHOD == 'REGISTER':
        LINE = METHOD + ' sip:' + username + ':' + uaserv_port
        LINE += ' SIP/2.0\r\n' + 'Expires:' + OPTION + '\r\n\r\n'
    elif METHOD == 'INVITE':
        LINE = METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n'
        SDP = 'Content-Type: application/sdp\r\n\r\n'
        SDP += 'v=0\r\n' + 'o=' + username + ' ' + uaserv_ip + '\r\n'
        SDP += 's=sesion prueba\r\n' + 't=0\r\n'
        SDP += 'm=audio ' + audio_port + ' RTP\r\n\r\n'
        LINE += SDP
    elif METHOD == 'BYE':
        LINE = METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n\r\n'
    print('Enviando: ' + LINE)
    my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
    data = my_socket.recv(1024)  
    answer = data.decode('utf-8').split(' ')
    if answer[1] == '100':
        LINE = 'ACK' + ' sip:' + OPTION + 'SIP/2.0\r\n\r\n'
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
    print(data.decode('utf-8'))
    print("Terminando socket...")

print("Fin.")
        
