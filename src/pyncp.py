#!/usr/bin/env python
from socket import * #@UnusedWildImport
import tarfile
import select
import struct
import sys #@Reimport
import os.path #@Reimport
import time 
''' VARIABLES TO MODIFY '''

# to be compatible with the original npush/npoll you will need to send the tar-file without compression
# still if we already use tar, why not use it with compression altogether ( e.g. gzip )
# we can be pretty sure that every modern os has gzip installed
# add -z in the npush/npoll sources to achieve this or use a pipe

#change this if you want more performance
wantCompress = False


TARWRITE='w|'

TARREAD= 'r|'

doWantBroadcast = True
wantFull=True
''' END VARIABLES TO MODIFY '''



#224.'n'.'c'.'p'
IPV4GROUP = '224.110.99.112'
IPV4BC = '255.255.255.255'

VERSIONSTRING="0.1"
PROGRAMNAME="pyncp"
PYNCPPORT=8002
MCMESSAGE="Multicasting for %s Version %s"%(PROGRAMNAME,VERSIONSTRING)
BCMESSAGE="Broadcasting for %s Version %s"%(PROGRAMNAME,VERSIONSTRING)


"""
not really helped in that way
class mainAsThread(Thread):
    '''
    dummy class to be able to use "high level threading interface"
    '''
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        main()
"""
def main(args):
    '''
    run pyncp directly, means user want to use direct copy
    '''
    
    # we have to rewrite TARREAD and TARWRITE 
    # to check if wantCompress changed in process
    global TARWRITE,TARREAD
    TARWRITE='w|gz' if wantCompress else 'w|'
    TARREAD='r|gz' if wantCompress else 'r|'
    # no arguments given --> listener mode
    if sys.argv.__len__() == 1 :
        server = pyncpListener()
        server.listen()
    elif sys.argv[1] == "push":
        try:
            checkFilesExist(sys.argv[2:])
        except:
            print "one of the files does not exist..."
        client = pyncpPusher()
        client.push(sys.argv[2:])
    elif sys.argv[1] == "poll" or sys.argv[1] == "pull" : # convenience feature as i always mix these two up

        server = pyncpListener()
        server.poll()
        
    elif sys.argv[1] == '--version':
        version()
        exit()
    elif sys.argv[1] == '--help':
        help()
        exit()
    #useful arguments given --> Client mode
    else:
        client = pyncpPusher()
        # push to given ip
        if sys.argv.__len__() < 3 :
            print "must provide an address plus at least one file to push"
        client.copyTo(sys.argv[1], sys.argv[2:])

def bindTCP():
    host = ''
    v4datasock = socket(AF_INET,SOCK_STREAM)

    v4datasock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    if hasattr(socket,"SO_REUSEPORT"):
        v4datasock.setsockopt(SOL_SOCKET,socket.SO_REUSEPORT,1)
    
    v4datasock.bind((host,PYNCPPORT))
    v4datasock.listen(1)    
    return v4datasock 


def closeFds(fds):
    '''
    Tries to close fds from the given field
    This field should contain references to the socket objects that should be closed
    '''
    #graceful close 
    time.sleep(1)
    for fd in fds:
        try:
            fd.close()
        except :
            print "one attrubute does not support close() or is already closed"

def checkFilesExist( files ):
    '''
    Convenience function to check if all files actually exist
    '''
    for f in files:
        if not os.path.exists(f):
            print "file",f,"does not exist. Exiting..."
            raise NameError('File does not exist')
    return

def version():
    print  PROGRAMNAME,"(simple Client/Server) Version",VERSIONSTRING
def help():
    version()
    print ""
    print "Usage:"
    print "      pyncp                    -- runs in listener mode, waits for connection"
    print "      pyncp [ip] [files]+      -- sends files to ip where pyncp should run in listener mode ( no args )"
    print "      pyncp push [files]+      -- broadcasts for clients, waits for connection"
    print "      pyncp poll               -- waits for broadcast, connects to broadcaster"

'''
Simple NCP Pusher class

It will create a compressed tar file and send it over a socket
to a given address

@author: Felix Richter
'''
class pyncpPusher:
    '''
    the pusher class
    ''' 

    def __init__(self):
        '''
        Constructor
        '''
    def copyTo(self, ip, files):
        '''
        Client Mode ( IP address given )
        '''
        print "[*] copying",files,"to ip :",ip
        try:
            sock = create_connection((ip,PYNCPPORT))
        except:
            print "[!] cannot create connection to host, bailing out"
            return
        sockfile = sock.makefile()
        t = tarfile.open('',TARWRITE,sockfile)
        print "[#] start writing files"
        f = 0
        try:
            for f in files:
                print "[*] adding:",f
                t.add(f)
            print "[#] finished"
        except:
            print "[!] failed while trying to add",f
            
        t.close()

       
        # sometimes closefds breaks the last bit of the connection, 
        # so we just "exit(0)" to avoid this
        closeFds((sock,sockfile))

        
        
    def push(self,files): 
        '''
        does broadcast/multicast to the network hoping that
        someone polls for the file and connects to the local address
        '''
        sock = -1
        address = -1
        v4mcsock = self.bindMulticastSock()
        
        if not v4mcsock or doWantBroadcast:
            v4bcsock = self.bindBroadcastSock()
            
        if not v4mcsock and not v4bcsock:
            print "[!]cannot continue without at least one announcement socket!"
            return (1)
            
        v4datasock = bindTCP()
        if not v4datasock:
            print "[!]cannot continue without data socket"
            return -1
        print "[*] starting X-Casting, waiting for TCP connect"
        while sock == -1:
            if v4mcsock:
                v4mcsock.sendto(MCMESSAGE,0,(IPV4GROUP,PYNCPPORT))
            if v4bcsock:
                v4bcsock.sendto(BCMESSAGE,0,(IPV4BC,PYNCPPORT))
            print ".",
            ready,output,exception = select.select([v4datasock],[],[],2) #@UnusedVariable
            for s in ready:
                '''
                if s == v4mcsock:
                    print "got connection on udp socket"
                    (sock,address) = v4mcsock.accept()
                    print "got : ",sock.recv(1024);
                    sock.close()
                '''
                
                if s == v4datasock:
                    (sock,address) = v4datasock.accept()
                    sock.settimeout(3)
                    try:
                        print "[*] Got connection from %s:%d"%address
                        print "[*] Client answer: %s"%sock.recv(1024)
                    except :
                        pass
        
        #after received connection
        
        print "[#] pushing",files,"to ",address[0],":",address[1]
        closeFds((v4datasock,v4mcsock,v4bcsock))
        
        sockfile = sock.makefile()
        
        t = tarfile.open('',TARWRITE,sockfile)
        tarfile.TarInfo.path
        print "[*] start writing files"
        for f in files:
            print "[*] adding:",f
            t.add(f)
            
        print "[*] finished"
        
        # IMPORTANT: close tar file after finished writing
        # otherwise the stream would be empty ...
        t.close()
        #exit(0)
        closeFds((sock,sockfile))
    
    def bindMulticastSock(self):
        host = ''
        # ipv4 multicast udp stuff
        v4mcsock = socket(AF_INET,SOCK_DGRAM,  IPPROTO_UDP)
        v4mcsock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        if hasattr(socket,"SO_REUSEPORT"):
            v4mcsock.setsockopt(SOL_SOCKET,socket.SO_REUSEPORT,1)
        
        v4mcsock.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 32)
    
        v4mcsock.bind((host,PYNCPPORT))
        v4mcsock.setsockopt(IPPROTO_IP,IP_MULTICAST_LOOP,1)
        return v4mcsock
    
    def bindBroadcastSock(self):
        host=''
        v4bcsock = socket(AF_INET,SOCK_DGRAM)
        v4bcsock.setsockopt(SOL_SOCKET,SO_BROADCAST,1)
        v4bcsock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        if hasattr(socket,"SO_REUSEPORT"):
            v4bcsock.setsockopt(SOL_SOCKET,socket.SO_REUSEPORT,1)
        v4bcsock.bind((host,PYNCPPORT))
        return v4bcsock
        
        
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
        
        tar czf - FILE | nc localhost 40101
        
        waits for a connection and then extracts the given file
        will wait until the socket is closed by the pusher
        
        @author:  felix
        '''
        
        #we create a new socket if the given socket is not yet open
        
        print "[#] Pyncp Listener: creating new connection"
        l = bindTCP()
        print "[*] waiting for connections"
        
        (sock, address) = l.accept()
        print "[*] connection from %s:%d"%address
        print "[*] receiving..."
        #receive the tar file and extract it
        sockfile = sock.makefile()
        t = tarfile.open('',TARREAD,sockfile)
        
        for tarinfo in t :
            # only extract with full paths if we actually want this
            tarinfo.name = tarinfo.name if wantFull else os.path.basename(tarinfo.name)
            print "[*]",tarinfo.name + ("/" if tarinfo.isdir() else "")
            try:
                t.extract(tarinfo)
            except:
                print "cannot extract:",tarinfo
        print "[#] received: "


        print "[#] finished"
        # we want the tarfile to close before all other sockets
        t.close() 
        #exit(0)
        closeFds((sock,sockfile,l))

        
    def poll(self):
        addr = -1
        v4mcsock = self.joinMulticast()
        print "[*] waiting for something-cast"
        while True:
            try:
                
                (data,addr) = v4mcsock.recvfrom(1024)
                if ( addr[1] == PYNCPPORT):
                    print "[*] found pusher at %s:%d"%addr
                    print "[#] Anouncement :",data
                    break
                else:
                    print "[?] received garbage from %s:%d"%addr
            except socket.error, e:
                print "exception",e
        
        v4mcsock.close()
        sock = socket(AF_INET,SOCK_STREAM,IPPROTO_TCP)
        
        sock.connect(addr)
        sock.send("I am ready!")
        #print "",sock.recv(1024)
        sock.setblocking(True)
        sockfile = sock.makefile()
        
        t = tarfile.open('',TARREAD,sockfile)
        
        
        print "[#] received: "
        for tarinfo in t :
            # only extract with full paths if we actually want this
            tarinfo.name = tarinfo.name if wantFull else os.path.basename(tarinfo.name)
            print "[*]",tarinfo.name + ("/" if tarinfo.isdir() else "")
            try:
                t.extract(tarinfo)
            except:
                print "cannot extract:",tarinfo

        print "[#] finished"
        t.close()
        
        #exit(0)
        closeFds((sock,sockfile))
        
    
    def joinMulticast(self):
        '''
        This socket will also be able to receive broadcast!
        '''
        v4mcsock = socket(AF_INET,SOCK_DGRAM,  IPPROTO_UDP)
        
        v4mcsock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        if hasattr(socket,"SO_REUSEPORT"):
            print "got SO_REUSEPORT"
            v4mcsock.setsockopt(SOL_SOCKET,socket.SO_REUSEPORT,1)    
    
        v4mcsock.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 32) 
        v4mcsock.setsockopt(IPPROTO_IP, IP_MULTICAST_LOOP, 1)

        v4mcsock.bind(('', PYNCPPORT))
        print "[#] Joining Multicast group"
        mreq = struct.pack("4sl", inet_aton(IPV4GROUP), INADDR_ANY)
        v4mcsock.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
        return v4mcsock

if __name__ == '__main__':
    main(None)
