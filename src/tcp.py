import socket
import os
import sys
import logging
import signal
import subprocess
from termcolor import colored
import json
import time

def timestr(t=time.localtime()):
    return '{}/{}, {} @ {}:{}:{}'.format(t.tm_mon, t.tm_mday, t.tm_year, t.tm_hour, t.tm_min, t.tm_sec)

def arr2str(arr):
    result = ''
    for i, e in enumerate(arr):
        if i == len(arr) - 1:
            result += str(e)
        else:
            result += str(e) + ', '
    return result

def cowsay(msg, stream=sys.stdout, cow=''):
    if not cow:
        subprocess.call(['cowsay', str(msg)], stdout=stream)
    else:
        subprocess.call(['cowsay', '-f', str(cow), str(msg)], stdout=stream)

class OracleHandler(object):
    def __init__(self, client_fd, client_addr):
        self.socket = client_fd
        self.addr   = '{}:{}'.format(*client_addr)
        self.stream = self.socket.makefile('w+')

    def handle(self):

        try:
            log_fs = open('log.json', 'r')
            log = json.load(log_fs)
        except:
            log = {}

        # welcome message and prompt
        cowsay('''Welcome to Oracle 2.0, Study Edition
        Please state your name.''', self.stream)
        self.stream.write('> ')
        self.stream.flush()
        name = self.stream.readline().rstrip()

        t = timestr()

        if not name:
            return
        if name in log:
            logging.info('Adding to existing log entry')
            log[name].append([t, ''])
        else:
            logging.info('Creating new log entry')
            log[name] = [[t, '']]

        logging.info('The user claims to be: ' + name)

        # get password
        cowsay('''Oh, hi {}! I hear you\'re trying to study for a test.
        I\'ll help you out if you have the password. Otherwise, buzz off.'''.format(name),\
                self.stream)
        self.stream.write('password> ')
        self.stream.flush()
        password = self.stream.readline().strip()

        log[name][-1][1] = password
        logging.info('Dumping log')
        with open('log.json.new', 'w') as stream:
            json.dump(log, stream, indent=4)
            stream.flush()
        os.rename('log.json.new', 'log.json')

        if password != 'GoTeamVim!':
            cowsay('''Sorry pal, my friend CURLY must have given you the wrong password.
            He usually hangs out by the port, somewhere by 3000. Bye!''', self.stream)
        else:
            # prompt for quiz or review
            cowsay('Hey, you got it! Do you want me to [r]eview some concepts with you or give you a [q]uiz?', self.stream)
            self.stream.writelines('[r/q]> ')
            self.stream.flush()
            data = self.stream.readline().strip()
            logging.debug(colored('User gave answer: '+data, 'blue'))
            while data != 'r' and data != 'q':
                cowsay('Sorry, didn\'t catch that. Enter r or q.', self.stream)
                self.stream.writelines('[r/q]> ')
                self.stream.flush()
                data = self.stream.readline().strip()
            if data == 'r':
                self.review()
            elif data == 'q':
                self.quiz()

    def review(self):
        qs = [l for l in open('review.txt', 'r')]
        usrin = ''
        i = 0
        while usrin != 'q':
            i = i % len(qs)
            cowsay(qs[i], self.stream)
            self.stream.write('[n/p/q]> ')
            self.stream.flush()
            din = self.stream.readline().strip()
            if din == 'n':
                i += 1
            elif din == 'p':
                i -= 1
            elif din == 'q':
                cowsay('Thanks for stopping by!', self.stream)
                break
            else:
                pass

    def quiz(self):
        qs = json.load(open('quiz.json', 'r'))
        cowsay('Welcome to the quiz! I\'ll ask you questions, and you just type in the answers. If you need to give up on a quiestion, enter "g" and I\'ll show you the acceptable answers. You can press "q" to quit. Press "enter" when you\'re ready!', self.stream)
        self.stream.write('> ')
        self.stream.flush()
        _ = self.stream.readline().strip()
        for q in qs:
            cowsay(q, self.stream)
            self.stream.write('[g/q]> ')
            self.stream.flush()
            ans = self.stream.readline().strip().lower()
            if ans in qs[q]:
                cowsay('Well done! Press enter when you\'re ready to move on.', self.stream)
            elif ans == 'g':
                cowsay('Here\'s what I got: {}. Press enter when you\'re ready to move on.'\
                        .format(arr2str(qs[q])), self.stream)
            elif ans == 'q':
                break
            else:
                cowsay('Better luck next time. Press enter when you\'re ready to move on.',\
                        self.stream)
            self.stream.write('> ')
            self.stream.flush()
            _ = self.stream.readline()
        cowsay('That\'s all I have for now. Come back in a little bit and I\'ll probably have a few more questions!', self.stream)

class CurlyHandler(OracleHandler):
    def handle(self):
        req = self.stream.readline().rstrip()
        logging.info('Got request: %s', req)
        req = req.split(' ')
        if len(req) != 3 or req[2] != 'HTTP/1.0' and req[2] != 'HTTP/1.1':
            cowsay('We ain\'t even speakin\' the same language. Bye!', self.stream, 'cows/sheep.cow')
        elif req[0] != 'GET':
            cowsay('I can only help you if you want to GET something. Bye.', self.stream, 'cows/sheep.cow')
        elif req[1] != '/password':
            cowsay('Come back when you want to GET your password. Bye', self.stream, 'cows/sheep.cow')
        else:
            cowsay('''I don't have your password, but I have this:
            R29UZWFtVmltIQo=
            Good luck!''', self.stream, 'cows/sheep.cow')


class TCPServer(object):
    def __init__(self, port, address, handler=OracleHandler):
        self.port       = port
        self.address    = address
        self.host       = (address, port)
        self.handler    = handler

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        try:
            self.socket.bind(self.host)
            self.socket.listen(0)
        except BaseException as err:
            logging.critical('Unable to bind socket: %s', err)
            sys.exit(1)

        logging.info('Listening to %s:%d', self.address, self.port)

        while True:
            logging.info(colored('Waiting for incoming connection', 'green'))
            client, addr = self.socket.accept()
            logging.info('Incoming connection: %s:%s', *addr)

            signal.signal(signal.SIGCHLD, signal.SIG_IGN)

            try:
                logging.debug('Forking...')
                pid = os.fork()
            except OSError as err:
                logging.critical('Unable to fork: %s', err)
                sys.exit(1)

            if pid == 0: # child
                handler = self.handler(client, addr)
                handler.handle()
                sys.exit(0)
            else:
                client.close()

class HTTPServer(TCPServer):
    def __init__(self, docroot='./html'):
        TCPServer.__init__(self, 2999, '0.0.0.0', CurlyHandler)
        self.docroot = docroot

    def run(self):
        try:
            self.socket.bind(self.host)
            self.socket.listen(0)
        except BaseException as err:
            logging.critical('HTTP Unable to bind socket: %s', err)
            sys.exit(1)

        logging.info('HTTP listening to %s:%d', *self.host)

        while True:
            logging.info('HTTP Waiting for incoming connection')
            client, addr = self.socket.accept()

            signal.signal(signal.SIGCHLD, signal.SIG_IGN)

            try:
                logging.debug('HTTP Forking...')
                pid = os.fork()
            except OSError as err:
                logging.critical('HTTP Unable to fork: %s', err)
                sys.exit(1)

            if pid == 0: #child
                handler = self.handler(client, addr)
                handler.handle()
                sys.exit(0)
            else:
                client.close()
