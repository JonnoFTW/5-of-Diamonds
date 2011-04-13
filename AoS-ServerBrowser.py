#!/usr/bin/python
import pygtk
import subprocess
pygtk.require('2.0')
import gtk
#import sys
import urllib
import _winreg

try:
    aos_key =  _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Classes\aos\shell\open\command')
    aos_path = _winreg.EnumValue(aos_key,0)[1].split('\" \"')[0][1:]
except:
    aos_path = 'C:\Program Files\Ace of Spades\client.exe'

class Base:
    def delete_event(self, widget,event, data=None):
        return False
    
    def destroy(self, widget, data=None):
        gtk.main_quit()
        
    def joinGame(self,widget, row,col):
        model = widget.get_model()
        try:
            self.statusbar.push(0,"Launching game")
            subprocess.Popen([aos_path, '-'+model[row][0]])
        except OSError,e:
            self.statusbar.push(0,str(e))
        return True
    
    def refresh(self,widget=None,data=None):
        try:
            servers = []
            page = urllib.urlopen('http://ace-spades.com/').readlines()
            s = page[page.index("<br>Server Listing:</p>\n")+1:-1]
            # Servers dict: [{'max':int,'playing':int,'name':str,'url':str}]
            for i in s:
                j = i.strip(' ').split()
                curr = i.replace(' ','').split('/')
                p = int(curr[0])
                m = int(curr[1][0:curr[1].find('<')])
                u = i[i.find('"')+1:i.rfind('"')]
                n = i[i.find('>')+1:i.rfind('<')-4]
                servers.append({
                    'max':m,
                    'playing':p,
                    'name':n,
                    'url':u})
            self.liststore.clear()
            for i in servers:
                self.liststore.append([i['url'],i['playing'],i['max'],i['name'],True])
            self.statusbar.push(0,"Updated successfully")
            return True
        except Exception, e:
            print e
            #update the server list with error message
            self.statusbar.push(0,"Updating failed")

    def draw_columns(self,treeview):
        rt = gtk.CellRendererText()
        self.tvurl = gtk.TreeViewColumn("URL",rt, text=0)
        self.tvurl.set_sort_column_id(0)
        rt = gtk.CellRendererText()
        self.tvmax = gtk.TreeViewColumn("Playing",rt, text=1)
        self.tvmax.set_sort_column_id(1)    
        rt = gtk.CellRendererText()
        self.tvcurr = gtk.TreeViewColumn("Max",rt, text=2)
        self.tvcurr.set_sort_column_id(2)
        rt = gtk.CellRendererText()
        self.tvname = gtk.TreeViewColumn("Name",rt, text=3)
        self.tvname.set_sort_column_id(3)
        for i in [self.tvurl,self.tvmax,self.tvcurr,self.tvname]:
            treeview.append_column(i)
                
    
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(450,450)
        self.window.set_title("5 of Diamonds")
        try:
            self.window.set_icon_from_file("diamonds.png")
        except Exception, e:
            print e.message
          #  sys.exit(1)
        self.window.connect("delete_event",self.delete_event)
        self.window.connect("destroy",self.destroy)
        self.window.set_border_width(10)
        self.statusbar = gtk.Statusbar()
        self.sw = gtk.ScrolledWindow()
        self.sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        self.liststore = gtk.ListStore(str, int, int,str, 'gboolean')
        self.treeview = gtk.TreeView(self.liststore)
        self.refresh()
        self.treeview.connect("row-activated",self.joinGame)
        self.treeview.set_search_column(0)
        self.draw_columns(self.treeview)

        self.sw.add(self.treeview)
        self.table = gtk.Table(2,2)
        self.exitB = gtk.Button(stock=gtk.STOCK_CLOSE)
        self.exitB.connect_object("clicked",gtk.Widget.destroy, self.window)
        
        self.refreshB = gtk.Button("Refresh")
        self.refreshB.connect("clicked",self.refresh,None)



        


        self.vbox = gtk.VBox(False,5)
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(3)
        self.hbox.pack_start(self.exitB,False,False,0)
        self.hbox.pack_start(self.refreshB,False,False,0)
        self.vbox.pack_start(self.hbox,False,False,0)
        self.vbox.pack_start(self.sw,True,True,0)
        self.vbox.pack_start(self.statusbar, False, False, 0)

        # Contain everything in a single Vbox
        self.window.add(self.vbox)
        self.window.show_all()
        

    def main(self):
        gtk.main()

if __name__ == "__main__":
    base = Base()
    base.main()

D
A
A
B
B
B
B
B
B
this
yyi

