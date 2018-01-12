#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa user agent client
"""

import os
import sys
import socket
import hashlib
from xml.sax import make_parser
from uaserver import XMLHandler
from proxy_registrar import Log
from xml.sax.handler import ContentHandler


def checknonce(nonce):

    fun_check = hashlib.md5()
    fun_check.update(bytes(nonce, 'utf-8'))
    fun_check.update(bytes(passwd, 'utf-8'))
    fun_check.digest()
    return fun_check.hexdigest()

if __name__ == "__main__":
    try:
        METHOD = str.upper(sys.argv[2])
        CONFIG = sys.argv[1]
        OPTION = sys.argv[3]
        parser = make_parser()
        Handler = XMLHandler()
        parser.setContentHandler(Handler)
        parser.parse(open(CONFIG))
        configtags = Handler.get_tags()
    except IndexError:
        sys.exit('Usage: ' + 'python3 uaclient.py config method option')
    except FileNotFoundError:
        sys.exit('File not found')

    username = configtags[0][1]['username']
    passwd = configtags[0][1]['passwd']
    uaserv_ip = configtags[1][1]['ip']
    if uaserv_ip == '':
        uaserv_ip = "127.0.0.1"
    uaserv_port = str(configtags[1][1]['puerto'])
    audio_port = (configtags[2][1]['puerto'])
    proxy_ip = configtags[3][1]['ip']
    proxy_port = int(configtags[3][1]['puerto'])
    file_log = configtags[4][1]['path']
    audio = configtags[5][1]['path']
    log = Log(file_log)
    log.start()

try:
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
            SDP += 's=sesion\r\n' + 't=0\r\n'
            SDP += 'm=audio ' + audio_port + ' RTP\r\n\r\n'
            LINE += SDP
        elif METHOD == 'BYE':
            LINE = METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n\r\n'
        else:
            sys.exit("Peticion Incorrecta")
        print('Enviando: ' + LINE)
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        log.sent_to(proxy_ip, proxy_port, LINE)
        data = my_socket.recv(1024)
        print(data.decode('utf-8'))
        receive = data.decode('utf-8').split()
        log.received_from(proxy_ip, proxy_port, data.decode('utf-8'))
        if receive[1] == '401':
            nonce = receive[-1].split('=')[1]
            response = checknonce(nonce)
            LINE += 'Authorization: Digest response = ' + response + '\r\n\r\n'
            my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
            log.sent_to(proxy_ip, proxy_port, LINE)
            data = my_socket.recv(1024)
            print('Envio autorizacion: ' + LINE)
            print(data.decode('utf-8'))
        elif receive[1] == '100':
            aud_port_emisor = receive[-2]
            LINE = 'ACK' + ' sip:' + OPTION + ' SIP/2.0\r\n\r\n'
            my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
            log.sent_to(proxy_ip, proxy_port, LINE)
            data = my_socket.recv(1024)
            print('Envio ack: ' + LINE)
            print(data.decode('utf-8'))
            RTP = './mp32rtp -i ' + uaserv_ip + ' -p '
            RTP += aud_port_emisor + " < " + audio
            log.ejecutando(RTP)
            print('Ejecutando... ', RTP)
            os.system(RTP)
except IndexError:
    error = ('SIP/2.0 404 User Not Found\r\n\r\n')
    log.error(error)
    sys.exit(error)

except ConnectionRefusedError:
    error = "No server listening at " + proxy_ip + ' port ' + str(proxy_port)
    log.error(error)
    sys.exit(error)

log.finish()
print("Terminando socket...")

print("Fin.")
