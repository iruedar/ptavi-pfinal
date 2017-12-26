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
    print(Handler.get_tags())
