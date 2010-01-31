
import sys
import socket
import pyncpmain as glob
import tarfile

import time

'''
Simple NCP Pusher class

It will create a compressed tar file and send it over a socket
to a given address

@author: Felix Richter
'''
def version():
    print  glob.PROGRAMNAME,"(simple Client/Server) Version",glob.VERSIONSTRING
def help():
    version()
    print ""
    print "without args, the pyncp listener will be started and listens for oncoming connections"
    print "    otherwise you have to provide a hostname/ip as first argument and"
    print "    the files to send as the next elements"

class pyncpPusher:
    '''
    the pusher class
    '''

    def __init__(self):
        '''
        Constructor
        '''
    def push(self, ip, files):
        print "pushing ",files," to ip : ",ip
        sock = socket.create_connection((ip,glob.PYNCPPORT))
        sockfile = sock.makefile()
        t = tarfile.open('','w|gz',sockfile)
        print "start writing files"
        for f in files:
            t.add(f)
        print "finished"
        t.close()
        sockfile.close()
        sock.close()
                                     
    
'''
Simple NCP Listener Class

It will listen on a socket for a connection and untar the given file stream

@author: Felix Richter
'''

class pyncpListener:
    '''
    the listener class
    '''
    
    def __init__(self):
        '''
        constructor
        '''
        
    
    def listen(self):
        '''
        Listens for a generous peer, this can also be a 
        
        tar cf - FILE | nc localhost 40101
        
        waits for a connection and then extracts the given file
        will wait until the socket is closed by the pusher
        
        @author:  felix
        '''
        
        print "Pyncp Listener: waiting for connections"
        l = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        l.bind((socket.gethostname(),glob.PYNCPPORT))
        l.listen(1)
        (sock, address) = l.accept()
        print "connection from ",address
        print "receiving..."
        #receive the tar file and extract it
        sockfile = sock.makefile()
        t = tarfile.open('','r|gz',sockfile)
        t.extractall()
        print "finished"
        
        t.close()
        sockfile.close()
        sock.close()
        l.close()
        
        

if __name__ == '__main__':
    '''
    run pyncp directly, means user want to use direct copy
    '''
    # no arguments given --> listener mode
    if sys.argv.__len__() == 1 :
        server = pyncpListener()
        server.listen()
    elif sys.argv[1] == '--version':
        version()
        exit()
    elif sys.argv[1] == '--help':
        help()
        exit()
    #useful arguments given --> pusher mode
    else:
        client = pyncpPusher()
        # push to given ip
        if sys.argv.__len__() < 3 :
            print "must provide an address plus at least one file to push"
        client.push(sys.argv[1], sys.argv[2:])