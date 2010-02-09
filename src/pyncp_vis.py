#!/usr/bin/env python
'''
Created on Feb 8, 2010

most of the examples are from java2s.com/Code/Python/GUI-TK/

@author: makefu
'''
from Tkinter import * #@UnusedWildImport
from tkFileDialog import askopenfiles
import tkMessageBox
import os
import pyncp
import socket
import sys
import thread

class WriteableObject:
    '''
    A Class for a writable Object.
    
    Lessons Learned:
    To replace stdout, just create a class with
    a "write" function in it. This does the magic!
    
    also you can do stuff like
    print >> writeableObj "hello, world!"
    '''
    def __init__(self,content):
        self.content = content
    def write(self,string):
        self.content.set( self.content.get() + string )

def appendUserFiles ( list ):
    '''
    Appends User selected files to a list
    '''
    
    paths = askopenfiles(filetypes=[("Wildcard", "*")])
    if paths == None:
        print "[?] No files chosen. Try again"
        return False
    print "[#] adding args",
    
    for path in paths:
        sys.argv.append(os.path.relpath(path.name))
    return True
        
def readFromShell(toWriteOn):
    '''
    replaces the original stdout with placebo writable Object
    this object will change the StringVar from the status window
    '''
    f = WriteableObject(toWriteOn)
    sys.stdout = f
    
    
    
class radiobuttons(Frame):
    choose = [('Pyncp Client',0,TOP),('Pyncp Server',1,TOP),('Pyncp Poll',2,TOP),('Pyncp Push',3,TOP) ]
    def __init__(self,parent=None):
        Frame.__init__(self, parent)
        self.choice = IntVar()
        self.wantCompression = BooleanVar()
        self.wantCompression.set(True)
        self.wantFullPaths = BooleanVar()
        self.choice.set(2)
        self.pack()
        self.make_widgets()
    
    def make_widgets(self):
        Label(self,text="Choose your destiny:").pack()
        for text,value,side in self.choose:
            rad = Radiobutton(self,text=text,value=value,variable=self.choice,indicatoron=0,anchor=W)
            rad.pack(side=side,expand=YES,fill=X)
        
        Checkbutton(self,text="compression",variable=self.wantCompression).pack(side=RIGHT,anchor=W)
        Checkbutton(self,text="full paths",variable=self.wantFullPaths).pack(side=RIGHT,anchor=W)
        
    def getState(self):
        return ( self.choice.get(), self.wantCompression.get(),self.wantFullPaths.get() )
            
   
if __name__ == '__main__': 
    ''' 
    This whole thing is a big hack and more like try and error.
    Still, i love my bastard child :3
    
    '''
    worker = 0 # the id of the worker thread
    root = Tk()
    
    root.title("pyncp vis")
    t = StringVar()     # for the ip address
    content=StringVar() # for the status window
    okText = StringVar() # for the button
    
    #new window
    statusWindow = Toplevel()
    statusWindow.title("Status Window")
    statusWindow.minsize(width=300,height=150)
    l = Label(statusWindow, font=("monospace",9),bg="white", textvariable=content,justify=LEFT,anchor=NW)
    content.set("[*] pyncp started in visual mode\n")
    l.pack(side=TOP,fill=BOTH,expand=YES)
    readFromShell(content)
    root.minsize(width=200,height=100)
    def doPress():
        
        sys.argv = []
        sys.argv.append("pyncp.py") 

        (ch,compr,full) = bar.getState()

        if ch == 0 : # CLIENT MODE 
            
            print "[#] client mode. Server is:",t.get()
            try:
                # the first address tuple, the 4. entry ( which is ip/port ) and then the IP
                resolved=socket.getaddrinfo(t.get(),None)[0][4][0]
                print "[#] resolved address is :",resolved
            except:
                #tkMessageBox.showwarning("Cannot resolve input", "Cannot resolve input string : `` %s `` !"%t.get())
                print "[!] unable to resolve address!"
                return
            sys.argv.append(resolved)
            if not appendUserFiles(sys.argv):
                return
                
        elif ch == 1:
            print "[#] server mode."
            #we do nothing here. pyncp will run in server mode with no args given
            
        elif ch == 2:
            print "[#] poll mode."
            sys.argv.append("poll")
        elif ch == 3:
            print "[#] push mode."
            sys.argv.append("push")
            if not appendUserFiles(sys.argv):
                return
        # Rewrite the global variables of the pyncp namespace
        # TODO: change this
        print "[#] compression:",compr
        pyncp.wantCompress = compr
        print "[#] full paths:",full
        pyncp.wantFull = full
        print "[#] new sys.argv :",sys.argv
        print "[*] running pyncp with new arguments"
        
        try:
            ''' 
            i found no really reliable way to kill a thread,
            fuck it let the user do what he wishes
            '''
            worker = thread.start_new_thread(pyncp.main, (None,))
        except:
            print "[!] something went wrong with the new thread :("
        okText.set("Run Pyncp again (are you sure you want that?)")
        
    
    
    bar = radiobuttons(root)
    
    okButton = Button(root, textvariable=okText, command=doPress)
    okText.set('Run Pyncp')
    okButton.pack(side=BOTTOM,fill=X)
    
    ipframe = Frame(root)
    Label(ipframe,text='IP address').pack(side=LEFT)
    
    Entry(ipframe,textvariable=t,bg='white').pack(side=RIGHT)
    
    ipframe.pack(fill=X,side=BOTTOM)
        
    root.mainloop()
    
