#!/usr/bin/python
import pygtk
import subprocess
pygtk.require('2.0')
import gtk
import urllib
import _winreg
import threading
import webbrowser

gtk.gdk.threads_init()

try:
    aos_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Classes\aos\shell\open\command')
    aos_path = _winreg.EnumValue(aos_key,0)[1].split('\" \"')[0][1:]
    config_path = aos_path.replace('client.exe','config.ini')
except:
    aos_path = 'C:\Program Files\Ace of Spades\client.exe'
    config_path = aos_path.replace('client.exe','config.ini')

class Update(threading.Thread):
     def __init__(self, list, statusbar):
         super(Update, self).__init__()
         self.list = list
         self.statusbar = statusbar
     
     def run(self):
         self.list.clear()
         gtk.gdk.threads_enter()
         try:
            servers = []
            page = urllib.urlopen('http://ace-spades.com/').readlines()
            s = page[page.index("<br>Server Listing:</p>\n")+2:-2]
            # Servers dict: [{'max':int,'playing':int,'name':str,'url':str}]
            for i in s:
                ratio = i[0:5].split('/')
                p = ratio[0].replace(' ','')
                m = ratio[1].replace(' ','')
                u = i[i.find('"')+1:i.rfind('"')]
                n = i[i.find('>')+1:i.rfind('<')-4]
                if i.find('<') >= 8 :
                    ping = i[6:i.find('<')]
                else:
                    ping = 0
                    
                self.list.append([u,int(ping),int(p),int(m),n,True])
            self.statusbar.push(0,"Updated successfully")
            return True
         except Exception, e:
            print e
            self.statusbar.push(0,"Updating failed (%s)" % (str(e)))

         finally:
            gtk.gdk.threads_leave()

class Base:
    def delete_event(self, widget,event, data=None):
        return False
    
    def destroy(self, widget, data=None):
        gtk.main_quit()
        
    def loadConfig(self):
        try:
            f = open(config_path,'r')
            lines = f.readlines()               
            self.xresE.set_text(lines[0].split()[1])
            self.yresE.set_text(lines[1].split()[1])
            self.nameE.set_text(lines[3].split()[1])
            self.volE.set_text(lines[2].split()[1])
            self.statusbar.push(0,"Loaded config.ini successfully")
            f.close()
        except Exception,e:
            self.statusbar.push(0,str(e))

    def updateConfig(self,widget,data=None):
        # Update the config file
        try:
            x = self.xresE.get_text()
            y = self.yresE.get_text()
            name = self.nameE.get_text()
            vol = self.volE.get_text()
            f = open(config_path,'w')
            f.write('\n'.join(['xres '+x,'yres '+y,'vol '+vol,'name '+name]))
            f.close()
            self.statusbar.push(0,"Config updated successfully")

        except Exception, e:
            self.statusbar.push(0,str(e))
    def openPage(self,widget,data=None):
        if data == 'aos':
            webbrowser.open_new_tab('http://ace-spades.com/')
        elif data == '5od':
            webbrowser.open_new_tab('http://www.reddit.com/r/AceOfSpades/comments/gouh3/update_aos_server_browser/')
        return True
    
    def joinGame(self,widget, row,col):
        model = widget.get_model()
        try:
            global aos_path
            self.statusbar.push(0,"Launching game")
            subprocess.Popen([aos_path, '-'+model[row][0]])
        except OSError,e:
            self.statusbar.push(0,str(e))
        return True
    
    def refresh(self,widget=None,data=None):
        self.liststore.append(['test',255,1,32,'test',True])
        t = Update(self.liststore,self.statusbar)
        t.start()
        return True

    def draw_columns(self,treeview):
        rt = gtk.CellRendererText()
        self.tvurl = gtk.TreeViewColumn("URL",rt, text=0)
        self.tvurl.set_sort_column_id(0)
        rt = gtk.CellRendererText()
        self.ping = gtk.TreeViewColumn("Ping",rt, text=1)
        self.ping.set_sort_column_id(1)
        rt = gtk.CellRendererText()
        self.tvmax = gtk.TreeViewColumn("Max",rt, text=3)
        self.tvmax.set_sort_column_id(2)
        rt = gtk.CellRendererText()
        self.tvcurr = gtk.TreeViewColumn("Playing",rt, text=2)
        self.tvcurr.set_sort_column_id(3)
        rt = gtk.CellRendererText()
        self.tvname = gtk.TreeViewColumn("Name",rt, text=4)
        self.tvname.set_sort_column_id(4)
        for i in [self.tvurl,self.ping,self.tvcurr,self.tvmax,self.tvname]:
            treeview.append_column(i)
                
    
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(550,450)
        self.window.set_title("5 of Diamonds")
        try:
            self.window.set_icon_from_file("diamonds.png")
        except Exception, e:
            print e.message
          # sys.exit(1)
        self.window.connect("delete_event",self.delete_event)
        self.window.connect("destroy",self.destroy)
        self.window.set_border_width(10)
        self.statusbar = gtk.Statusbar()
        self.sw = gtk.ScrolledWindow()
        self.sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        self.liststore = gtk.ListStore(str,int, int, int,str, 'gboolean')
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

        self.saveB = gtk.Button("Save Config")
        self.saveB.connect("clicked",self.updateConfig,None)
        
        self.webB = gtk.Button("AoS Webpage")
        self.webB.connect("clicked",self.openPage,'aos')

        self.appB = gtk.Button("Get Latest 5oD")
        self.appB.connect("clicked",self.openPage,'5od')
        
        #stick the buttons in a frame at the bottom of the window
        #use a hbox of 3 vboxes
        # Could probably refactor this with some lists and iterations
        self.frame = gtk.Frame("Game Config")
        self.xresE = gtk.Entry()
        self.yresE = gtk.Entry()
        self.nameE = gtk.Entry()
        self.volE = gtk.Entry()
        self.lXres = gtk.Label("X Res")
        self.lYres = gtk.Label("Y Res")
        self.lName = gtk.Label("Name")
        self.lVolume = gtk.Label("Volume")
        
        self.forms = gtk.HBox()
        self.box1 = gtk.VBox(False,5)
        self.box2 = gtk.VBox(False,5)

        self.box1.pack_start(self.lXres,False,False,0)
        self.box1.pack_start(self.xresE,False,False,0)
        
        self.box1.pack_start(self.lYres,False,False,0)
        self.box1.pack_start(self.yresE,False,False,0)
        
        self.box2.pack_start(self.lName,False,False,0)
        self.box2.pack_start(self.nameE,False,False,0)
                        
        self.box2.pack_start(self.lVolume,False,False,0)
        self.box2.pack_start(self.volE,False,False,0)

        self.aboutFrame = gtk.Frame("About")
        self.abvbox = gtk.VBox(True,3)
        
        self.abtlbl = gtk.Label("5 of Diamonds\nVersion 1.4\n2011\nGot bugs? Get the latest version")
        self.abtlbl.set_justify(gtk.JUSTIFY_CENTER)
        self.abvbox.pack_start(self.abtlbl)

        self.aboutFrame.add(self.abvbox)
        
        # Add the boxes to the frame
        for i in [self.box1,self.box2]:
            self.forms.pack_start(i,False,False,0)
        self.forms.pack_start(self.aboutFrame,True,True,0)
        self.frame.add(self.forms)
        self.loadConfig()
        self.vbox = gtk.VBox(False,5)
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(3)
        self.hbox.pack_start(self.exitB,False,False,0)
        self.hbox.pack_start(self.refreshB,False,False,0)
        self.hbox.pack_start(self.saveB,False,False,0)
        self.hbox.pack_start(self.webB,False,False,0)
        self.hbox.pack_start(self.appB,False,False,0)
        self.vbox.pack_start(self.hbox,False,False,0)
        self.vbox.pack_start(self.sw,True,True,0)
        self.vbox.pack_start(self.frame,False,False,0)
        self.vbox.pack_start(self.statusbar, False, False, 0)

        # Contain everything in a single Vbox
        self.window.add(self.vbox)
        self.window.show_all()


    def main(self):
        gtk.main()

if __name__ == "__main__":
    base = Base()
    base.main()

