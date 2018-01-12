#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa user agent client
"""

import os
import sys
import socket
import socketserver
from xml.sax import make_parser
from proxy_registrar import Log
from xml.sax.handler import ContentHandler


try:
    CONFIG = sys.argv[1]
except IndexError:
    sys.exit('Usage: ' + 'python3 uaserver.py config')


class XMLHandler(ContentHandler):

    def __init__(self):     # Declaramos las listas de los elementos
        self.list_element = []
        self.element = {
            'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']}

    def startElement(self, name, element):      # Añade elementos
        dicc = {}
        if name in self.element:
            for elment in self.element[name]:
                dicc[elment] = element.get(elment, '')
            self.list_element.append([name, dicc])

    def get_tags(self):      # Devuelve la lista con elementos encontrados
        return self.list_element


class EchoHandler(socketserver.DatagramRequestHandler):

    rtp_port = []

    def handle(self):
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if len(line) == 0:
                break

            mnsg = line.decode('utf-8')
            receive = mnsg.split()
            METHOD = receive[0]
            METHODS = 'REGISTER', 'INVITE', 'ACK', 'BYE'
            if METHOD in METHODS:
                print(METHOD + ' recieved')
                log.received_from(proxy_ip, proxy_port, mnsg)
                if METHOD == 'INVITE':
                    self.rtp_port.append(receive[-2])
                    print(self.rtp_port)
                    print('enviamos invite')
                    self.wfile.write(b'SIP/2.0 100 Trying\r\n\r\n')
                    self.wfile.write(b'SIP/2.0 180 Ringing\r\n\r\n')
                    self.wfile.write(b'SIP/2.0 200 OK\r\n')
                    LINE = "Content-Type: application/sdp\r\n\r\n"
                    LINE += "v=0\r\no=" + username + " " + uaserv_ip
                    LINE += "\r\ns=sesion" + "\r\nt=0\r\nm=audio "
                    LINE += audio_port + " RTP"
                    SDP = (bytes(LINE, "utf-8"))
                    sent = 'SIP/2.0 100 Trying SIP/2.0 180 Ringing'
                    sent += ' SIP/2.0 200 OK ' + LINE
                    self.wfile.write(SDP)
                    log.sent_to(proxy_ip, proxy_port, sent)
                elif METHOD == 'ACK':
                    cvlc = 'cvlc rtp://@' + uaserv_ip + ':' + self.rtp_port[0]
                    log.ejecutando(cvlc)
                    print('Ejecutando... ', cvlc)
                    os.system(cvlc)
                    RTP = './mp32rtp -i ' + uaserv_ip + ' -p '
                    RTP += self.rtp_port[0] + " < " + audio
                    log.ejecutando(RTP)
                    print('Ejecutando... ', RTP)
                    os.system(RTP)
                elif METHOD == 'BYE':
                    msg = 'SIP/2.0 200 OK\r\n\r\n'
                    self.wfile.write(bytes(msg, 'utf-8'))
                    log.sent_to(proxy_ip, proxy_port, msg)
            elif METHOD not in METHOD:
                error = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(bytes(error, 'utf-8'))
                log.error(error)
            else:
                error = 'SIP/2.0 400 Bad Request\r\n\r\n'
                self.wfile.write(bytes(error, 'utf-8'))
                log.error(error)

if __name__ == "__main__":
    parser = make_parser()
    Handler = XMLHandler()
    parser.setContentHandler(Handler)
    parser.parse(open(CONFIG))
    configtags = Handler.get_tags()

    username = configtags[0][1]['username']
    passwd = configtags[0][1]['passwd']
    uaserv_ip = configtags[1][1]['ip']
    if uaserv_ip == '':
        uaserv_ip = "127.0.0.1"
    uaserv_port = int(configtags[1][1]['puerto'])
    audio_port = (configtags[2][1]['puerto'])
    proxy_ip = configtags[3][1]['ip']
    proxy_port = int(configtags[3][1]['puerto'])
    file_log = configtags[4][1]['path']
    audio = configtags[5][1]['path']
    log = Log(file_log)
    log.start()

    serv = socketserver.UDPServer((uaserv_ip, uaserv_port), EchoHandler)
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log.finish()
        print('servidor finalizado')
