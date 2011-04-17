#!/usr/bin/python
import pygtk
import subprocess
pygtk.require('2.0')
import gtk
import urllib
import threading
import webbrowser
import os

#It's safe to assume we're using a Linux system if importing _winreg fails
try:
    import _winreg
    onLinux = False
except:
    onLinux = True

gtk.gdk.threads_init()
global aos_path
global config_path

blacklist = []

if onLinux:
    #find some way to access Wine's registry. For now, just take a guess.
    aos_path = os.path.expanduser('~')+'/.wine/drive_c/Program Files/Ace of Spades/client.exe'
else:
    try:
        aos_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Classes\aos\shell\open\command')
        aos_path = _winreg.EnumValue(aos_key,0)[1].split('\" \"')[0][1:]
    except:
        aos_path = 'C:\Program Files\Ace of Spades\client.exe'

config_path = aos_path.replace('client.exe','config.ini')
blacklist_path = aos_path.replace('client.exe','blacklist.txt')

print "AoS client path: "+aos_path
print "AoS config path: "+config_path
print "5oD blacklist path: "+blacklist_path

def isascii(x):
    try:
        x.decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def loadBlacklist():
    try:
            lines = open(blacklist_path,'r').readlines()
            for i in lines:
                blacklist.append(i)
            print 'Loaded...'
    except:
            try:
                print 'Creating blacklist file: %s' % (blacklist_path)
                _file = open(blacklist_path,'w')
                _file.close()
                loadBlacklist()
            except:
                print "Could not make blacklist file"
    finally:
        print blacklist
        
loadBlacklist()

class Update(threading.Thread):
     def __init__(self, list, statusbar,checks):
         super(Update, self).__init__()
         self.list = list
         self.statusbar = statusbar
         self.checks = [c.get_label() for c in checks]
         
     def run(self):
         self.list.clear()
         gtk.gdk.threads_enter()
         global blacklist
         try:
            servers = []
            page = urllib.urlopen('http://ace-spades.com/').readlines()
            s = page[page.index("<pre>\n")+1:-2]
            # Servers dict: [{'max':int,'playing':int,'name':str,'url':str}]
            for i in s:
                try:
                    ratio = i[0:5].split('/')
                    p = int(ratio[0].replace(' ',''))
                    m = int(ratio[1].replace(' ',''))
                    u = i[i.find('"')+1:i.find('>')-1]
                    n = filter(lambda x: isascii(x),i[i.find('>')+1:i.rfind('<')])
                    if i.find('<') >= 8 :
                        ping = int(i[6:i.find('<')])
                    else:
                        ping = 0
                    if not n in blacklist:
                        if "Full" in self.checks and "Empty" in self.checks:
                            if p != m and p != 0:
                                self.list.append([u,ping,p,m,n,True])
                                continue
                        elif "Empty" in self.checks:
                            if p != 0:
                                self.list.append([u,ping,p,m,n,True])
                                continue
                        elif "Full" in self.checks:
                            if p != m:
                                self.list.append([u,ping,p,m,n,True])
                                continue                    
                        else:
                            self.list.append([u,ping,p,m,n,True])
                except:
                    print 'Skipped invalid server'
            self.statusbar.push(0,"Updated successfully")
            return True
         except Exception, e:
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
            self.statusbar.push(0,str(e)+ '| Tried: '+aos_path)
    
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
            self.statusbar.push(0,"Config updated successfully in: "+config_path )
        except Exception, e:
            self.statusbar.push(0,str(e)+ '| Tried: '+aos_path)
            
    def openPage(self,widget,data=None):
        if data == 'aos':
            webbrowser.open_new_tab('http://ace-spades.com/')
        elif data == '5od':
            webbrowser.open_new_tab('http://www.reddit.com/r/AceOfSpades/comments/gouh3/update_aos_server_browser/')
        return True
    
    def joinGame(self,url):      
        try:
            global aos_path
            global onLinux
            if onLinux:
                subprocess.Popen(['wine', aos_path, '-'+url])
            else:
                subprocess.Popen([aos_path, '-'+url])
            self.statusbar.push(0,"Launching game from: "+aos_path)
        except OSError,e:
            self.statusbar.push(0,str(e)+ '| Looked in '+aos_path)
        return True

        
    def launchServer(self,widget, data=None):
        try:
            self.statusbar.push(0,"Launching server from: "+aos_path[:-10]+'server.exe')
            subprocess.Popen([aos_path[:-10]+'server.exe'])
        except OSError,e:
            self.statusbar.push(0,str(e)+ '| Looked in '+aos_path[:-10]+'server.exe')
        return True
    
    def refresh(self,widget=None,data=None):
        #self.liststore.append(['Loading',0,0,0,'Refreshing',True])
        t = Update(self.liststore,self.statusbar,[r for r in self.checks if r.get_active()])
        t.start()
        return True
    
    def pop_path(self,widget=None,data=None):
        #popup a window asking for the directory
        self.pop = gtk.FileChooserDialog(title="Where did you install AoS?",
                                         action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                         buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        response = self.pop.run()
        if response == gtk.RESPONSE_OK or response == gtk.STOCK_OPEN:
            self.set_path(self.pop.get_filename())
        self.pop.destroy()
        return True
    
    def set_path(self,data=aos_path):
        aos_path = data+'\\client.exe'
        config_path = aos_path.replace('client.exe','config.ini')
        self.statusbar.push(0,'Now working from: '+aos_path[:-10])
        print "AoS client path: "+aos_path
        print "AoS config path: "+config_path        
        return True

    def get_selected_id(self):
        ids = []
        store, paths = self.treeview.get_selection().get_selected_rows()
        for path in paths:
            treeiter = store.get_iter(path)
            val = store.get_value(treeiter,4)
            ids.append(val)
        return ids
        
    def blacklistServer(self,menuitem,*ignore):
        values = self.get_selected_id()
        name = values[0]
        try:
            blacklist.append(name)
            f = open(blacklist_path,'a')
            f.write(name+'\n')
            f.close()
            self.statusbar.push(0,name+' added to blacklist')
        except Exception,e:
            self.statusbar.push(0,'Failed to add to blacklist: '+name+' | '+str(e))

    def serverListEvent(self,treeview,event):
        x = int(event.x)
        y = int(event.y)
        time = event.time
        model = treeview.get_model()
        pthinfo = treeview.get_path_at_pos(x, y)
        if pthinfo is not None:
            path, col, cellx, celly = pthinfo
            treeview.grab_focus()
            treeview.set_cursor( path, col, 0)
            # Popup blacklist menu on right click
            if event.button == 3:
                self.blackmenu.popup( None, None, None, event.button, time)
            # Join game on double click
            elif event.type == gtk.gdk._2BUTTON_PRESS:
                self.joinGame(model[path][0])
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
        #self.tvname.set_sort_column_id(4)
        for i in [self.tvurl,self.ping,self.tvcurr,self.tvmax,self.tvname]:
            treeview.append_column(i)
                
    
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(600,650)
        self.window.set_title("5 of Diamonds")
        try:
            self.window.set_icon_from_file("diamonds.png")
        except Exception, e:
            self.statusbar.push(0,"Error: "+str(e))
        self.window.connect("delete_event",self.delete_event)
        self.window.connect("destroy",self.destroy)
        self.window.set_border_width(10)
        self.statusbar = gtk.Statusbar()
        self.sw = gtk.ScrolledWindow()
        self.sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        self.liststore = gtk.ListStore(str,int, int, int,str, 'gboolean')
        self.treeview = gtk.TreeView(self.liststore)

        self.treeview.connect("button_press_event",self.serverListEvent)
        self.treeview.set_search_column(0)
        self.draw_columns(self.treeview)
        
        self.blackmenu = gtk.Menu()
        self.bitem = gtk.MenuItem("Blacklist server")
        self.blackmenu.append(self.bitem)
        self.bitem.connect("activate",self.blacklistServer)
        self.bitem.show()        

        self.sw.add(self.treeview)
        self.table = gtk.Table(2,2)
        self.exitB = gtk.Button(stock=gtk.STOCK_CLOSE)
        self.exitB.connect_object("clicked",gtk.Widget.destroy, self.window)
        
        self.refreshB = gtk.Button("Refresh")
        self.refreshB.connect("clicked",self.refresh,None)

        self.saveB = gtk.Button("Save Config")
        self.saveB.connect("clicked",self.updateConfig,None)

        self.serverB = gtk.Button("Launch Server")
        self.serverB.connect("clicked",self.launchServer,None)
        
        self.webB = gtk.Button("AoS Webpage")
        self.webB.connect("clicked",self.openPage,'aos')

        self.appB = gtk.Button("Get Latest 5oD")
        self.appB.connect("clicked",self.openPage,'5od')

        self.pathB = gtk.Button("Find Client.exe")
        self.pathB.connect("clicked",self.pop_path,None)
        
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
        
        self.abtlbl = gtk.Label("5 of Diamonds\nVersion 1.7\n2011\nGot bugs? Get the latest version")
        self.abtlbl.set_justify(gtk.JUSTIFY_CENTER)
        self.abvbox.pack_start(self.abtlbl)

        self.aboutFrame.add(self.abvbox)

       # self.radios = []
       #Pass this info into the update so it filters correctly
        self.filterFrame = gtk.Frame("Filters")
        self.filterBox = gtk.HBox()
        self.checkFull = gtk.CheckButton("Full",True)
        self.checkEmpty = gtk.CheckButton("Empty",True)
        self.checks = [self.checkFull,self.checkEmpty]
        for i in self.checks:
            self.filterBox.pack_start(i,False,False,0)
        self.helplbl = gtk.Label("Refresh after selecting filters; rightclick to blacklist a server")
        self.helplbl.set_justify(gtk.JUSTIFY_RIGHT)
        self.filterBox.pack_start(self.helplbl,True,True,0)
        self.filterFrame.add(self.filterBox)

        
        # Add the boxes to the frame
        for i in [self.box1,self.box2]:
            self.forms.pack_start(i,False,False,0)
        self.forms.pack_start(self.aboutFrame,True,True,0)
        self.frame.add(self.forms)
        self.loadConfig()
        self.vbox = gtk.VBox(False,5)
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(3)

        buttons =[self.exitB,self.refreshB,self.saveB,self.webB,self.appB,self.pathB,self.serverB]
        for i in buttons:
            self.hbox.pack_start(i,False,False,0) 
        self.vbox.pack_start(self.hbox,False,False,0)
        self.vbox.pack_start(self.sw,True,True,0)
        self.vbox.pack_start(self.frame,False,False,0)
        self.vbox.pack_start(self.filterFrame,False,False,0)
        self.vbox.pack_start(self.statusbar, False, False, 0)

        # Contain everything in a single Vbox
        self.window.add(self.vbox)
        self.window.show_all()
        self.refresh()

    def main(self):
        try:
            gtk.main()
        except:
            self.statusbar.push(0,"Error: "+str(e))    
if __name__ == "__main__":
    base = Base()
    base.main()