#!/usr/bin/python

import socket
import getopt
import sys
import os
import logging
import tcp

PORT = 1000

logging.basicConfig(format='%(asctime)s @ [%(lineno)d] (%(levelname)s): %(message)s', level=0)

def usage():
    print >>sys.stderr, '''Usage: server.py [p PORT -h]
Options:
    -p PORT     Specify port to listen to (default 1000)
    -h          Show this help message'''

try:
    opts, args = getopt.getopt(sys.argv[1:], 'hp:')
except getopt.GetoptError as err:
    logging.critical(err)
    usage()
    sys.exit(1)

logging.debug('Parsing command line arguments')
for o, a in opts:
    if o == '-h':
        usage()
        sys.exit(0)
    elif o == '-p':
        PORT = int(a)

logging.info('Using PORT %d', PORT)

logging.debug('Instantiating server')

try:
    oracle = tcp.TCPServer(PORT, '0.0.0.0')
    curly  = tcp.HTTPServer()
    logging.info('Successfully created server')
except BaseException as err:
    logging.critical('Unable to instantiate server: %s', err)
    sys.exit(1)


try:
    try:
        pid = os.fork()
    except OSError as err:
        logging.critical('Unable to fork: %s', err)
        sys.exit(1)
    if pid == 0:
        curly.run()
    else:
        oracle.run()
except KeyboardInterrupt as err:
    oracle.socket.shutdown(socket.SHUT_RDWR)
    oracle.socket.close()
    curly.socket.shutdown(socket.SHUT_RDWR)
    curly.socket.close()
    logging.warning('Exiting from SIGINT')
