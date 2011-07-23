#!/usr/bin/python
import pygtk
import subprocess
pygtk.require('2.0')
import gtk
import urllib
import threading
import webbrowser
import os,sys
VERSION = 1.86
#It's safe to assume we're using a Linux system if importing _winreg fails
global onLinux
try:
    import _winreg
    onLinux = False
except:
    onLinux = True

gtk.gdk.threads_init()
global aos_path
global config_path
global mouse_fix

blacklist = []
favlist = []

try:
    if sys.argv[1]=='-mousefix':
        mouse_fix = True
    else:
        mouse_fix = False
except:
    mouse_fix = False

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
favlist_path = aos_path.replace('client.exe','favourites.txt')

print "AoS client path: "+aos_path
print "AoS config path: "+config_path
print "5oD Blacklist path: "+blacklist_path
print "5oD Favourites path: "+favlist_path

def isascii(x):
    try:
        x.decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True
       
# aos2ip(aos): Converts an AoS address (aos://12345678) to a dotted IP address
def aos2ip(aos): 
  # Chop off the aos:// and convert the reversed decimal IP to a standard 4-dot IP
  ip = int(aos[6:])
  ip = str(ip&0xFF)+'.'+str((ip&0xFF00)>>8)+'.'+str((ip&0xFF0000)>>16)+'.'+str((ip&0xFF000000)>>24)
  return ip

def loadLists(blacklist=True,favlist=True):
    if blacklist:
        try:
                lines = open(blacklist_path,'r').readlines()
                for i in lines:
                    #remove the \n
                    blacklist.append(i[:-1])
                print 'Loaded blacklist ...'
        except:
                try:
                    print 'Creating blacklist file: %s' % (blacklist_path)
                    _file = open(blacklist_path,'w')
                    _file.close()
                    loadLists(favlist=False)
                except:
                    print "Could not make blacklist file"
    if favlist:
        try:
                lines = open(favlist_path,'r').readlines()
                for i in lines:
                    favlist.append(i[:-1])
                print 'Loaded favourites...'
        except Exception, e:
                print e
                try:
                    print 'Creating Favourites list file: %s' % (favlist_path)
                    _file = open(favlist_path,'w')
                    _file.close()
                    loadLists(blacklist=False)
                except:
                    print "Could not make Favourites file"
        
loadLists()

def log(txt):
	f = open('output.txt','a')
	f.write(txt+'\n')
	f.close()

log('Logging...')

class Update(threading.Thread):
     def stop(self):
        gtk.gdk.flush()
        gtk.gdk.threads_leave()
     def __init__(self, list, statusbar,checks,last_played = None):
         super(Update, self).__init__()
         self.list = list
         self.statusbar = statusbar
         self.checks = [c.get_label() for c in [r for r in checks if r.get_active()]]
         self.last_played = last_played
     def run(self):
        log('[thread] Entering run()')
        self.list.clear()
        log('[thread] List cleared.')
        global blacklist
        try:
            servers = []
            log('[thread] Grabbing ace-spades page...')
            page = urllib.urlopen('http://ace-spades.com/play/').readlines()
            log('[thread] Grabbed.')
            for entry in page: log(repr(entry))
            print 'testing %s' % (page.index("<pre>#/MAX PING NAME (Click to Join)\n"))
            s = page[page.index("<pre>#/MAX PING NAME (Click to Join)\n")+1:page.index("</pre>\n")]
            log('[thread] Parsing page...')
            for i in s:
                try:
                    ratio = i[0:5].split('/')
                    playing = int(ratio[0].replace(' ',''))
                    max_players = int(ratio[1].replace(' ',''))
                    url = i[i.find('"')+1:i.find('"',24)]
                    log('[thread] Parsing...')
                    fav = url in favlist
                    ip = aos2ip(url)
                    log('[thread] Performing ping.')
                    try:
                        if onLinux:
                            pipe = os.popen('ping %s -c 1 -w 1' % (ip))
                            ping = int(pipe.read().split('\n')[2].rpartition('time=')[2].rpartition(' ms')[0])
                            pipe.stdin.close()
                        else:
                            pipe = os.popen('ping %s -n 1 -w 100' % (ip))
                            ping = int(pipe.read().split('\n')[2].rpartition('time=')[2].rpartition('ms')[0])
                            pipe.stdin.close()
                    except:
                        ping = int(i[6:i.find('<')])
                    name = filter(lambda x: isascii(x),i[i.find('>')+1:i.rfind('<')])
                    if self.last_played == url: bg='#BFFFB8'
                    else: bg = '#FFFFFF'
                    server = [fav,url,ping,playing,max_players,name,ip,bg]
                    gtk.gdk.threads_enter()

                    if not url in blacklist:
                        if "Full" in self.checks and "Empty" in self.checks:
                            if playing != max_players and playing != 0:
                                self.list.append(server)
                        elif "Empty" in self.checks:
                            if playing != 0:
                                self.list.append(server)
                        elif "Full" in self.checks:
                            if playing != max_players:
                                self.list.append(server)
                        else:
                            self.list.append(server)
                    gtk.gdk.threads_leave()
                except Exception, e:
                    print 'Skipped invalid server (%s)' % (str(e))
            log('[thread] Pushing to statusbar...')
            gtk.gdk.threads_enter()
            self.statusbar.push(0,"Updated successfully")
            gtk.gdk.threads_leave()
            log('[thread] Done.')
            return True
        except Exception, e :#When it can't update the statusbar because it is dead, sys.exit()
            log('[thread] Exited with: %s' % (str(e)))
            print e
            sys.exit()
        except Exception, e:
            log('[error] %s' % (str(e())))
            gtk.gdk.threads_enter()
            self.statusbar.push(0,"Updating failed (%s)" % (str(e)))
            gtk.gdk.threads_leave()

        finally:
             pass

class Base:
    def delete_event(self, widget,event, data=None):
        return False
    
    def destroy(self, widget, data=None):
        gtk.main_quit()
        self.t.stop()
        sys.exit()
        return False
        
    def loadConfig(self):
        try:
            f = open(config_path,'r')
            lines = f.readlines()
            conf = dict()
            for i in lines:
                j = i.split()
                conf[j[0]] = j[1]
            self.xresE.set_text(conf['xres'])
            self.yresE.set_text(conf['yres'])
            self.nameE.set_text(conf['name'])
            self.volE.set_text(conf['vol'])
            self.caplim.set_text(conf['caplimit'])
            self.invert.set_text(conf['inverty'])
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
            inv = self.invert.get_text()
            caplim = self.caplim.get_text()
            f = open(config_path,'w')
            f.write('\n'.join(['name '+name,'xres '+x,'yres '+y,'vol '+vol,'inverty '+inverty,'caplimit '+caplim]))
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
            self.statusbar.push(0,"Launching game from: "+aos_path+' -'+url)
        except OSError,e:
            self.statusbar.push(0,str(e)+ '| Looked in '+aos_path)
        return True

    #Following two functions SHAMELESSLY copied from:
    #http://ardoris.wordpress.com/2008/07/05/pygtk-text-entry-dialog/
    def responseToDialog(self,entry, dialog, response):
        dialog.response(response)
    
    def getip(self,widget,data=None):
        #base this on a message dialog
        dialog = gtk.MessageDialog(
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_OK,
            None)
        dialog.set_markup('<b>IP2AoS</b>')
        #create the text input field
        entry = gtk.Entry()
        #allow the user to press enter to do ok
        entry.connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)
        #create a horizontal box to pack the entry and a label
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("IP:"), False, 5, 5)
        hbox.pack_end(entry)
        #some secondary text
        dialog.format_secondary_markup("Enter IP address.")
        #add it and show it
        dialog.vbox.pack_end(hbox, True, True, 0)
        dialog.show_all()
        #go go go
        dialog.run()
        text = entry.get_text()
        dialog.destroy()
        self.ip2aos(text)

    def ip2aos(self,ip):
        try:
            ip = ip.split('.')
            ip = int(ip[0]) + (int(ip[1])<<8) + (int(ip[2])<<16) + (int(ip[3])<<24)
            print ip
            self.joinGame('aos://%s' % (str(((ip + (1<<31)) % (1<<32)) - (1<<31))))
        except:
            print 'Invalid IP.'

    def launchServer(self,widget, data=None):
        try:
            self.statusbar.push(0,"Launching server from: "+aos_path[:-10]+'server.exe')
            subprocess.Popen([aos_path[:-10]+'server.exe'])
        except OSError,e:
            self.statusbar.push(0,str(e)+ '| Looked in '+aos_path[:-10]+'server.exe')
        return True
    
    def refresh(self,widget=None,data=None):
        self.t = Update(self.liststore,self.statusbar,self.checks,self.last_played)
        self.t.start()
        return True
    
##    def pop_path(self,widget=None,data=None):
##        #popup a window asking for the directory
##        self.pop = gtk.FileChooserDialog(title="Where did you install AoS?",
##                                         action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
##                                         buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
##        response = self.pop.run()
##        if response == gtk.RESPONSE_OK or response == gtk.STOCK_OPEN:
##            self.set_path(self.pop.get_filename())
##        self.pop.destroy()
##        return True
##    
##    def set_path(self,data=aos_path):
##        aos_path = data+'\\client.exe'
##        config_path = aos_path.replace('client.exe','config.ini')
##        self.statusbar.push(0,'Now working from: '+aos_path[:-10])
##        print "AoS client path: "+aos_path
##        print "AoS config path: "+config_path        
##        return True

    def get_selected_id(self):
        ids = []
        store, paths = self.treeview.get_selection().get_selected_rows()
        for path in paths:
            treeiter = store.get_iter(path)
            val = store.get_value(treeiter,1)
            ids.append(val)
        return ids
        
    def blacklistServer(self,menuitem,*ignore):
        values = self.get_selected_id()
        name = values[0]
        try:
            if not name in blacklist:
                blacklist.append(name)
                f = open(blacklist_path,'w')
                for i in blacklist:
                    f.write(i+'\n')
                f.close()
                self.statusbar.push(0,name+' added to blacklist')
            else:
                self.statusbar.push(0,name+' already in blacklist')
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
            elif event.type == gtk.gdk.BUTTON_PRESS and col.get_title() == 'Fav':
                it = model.get_iter(path)
                model[it][0] = not model[it][0]
                url = model[it][1]
                if model[it][0]:
                    #Put server in favourites if it isn't already
                    if url not in favlist:
                        favlist.append(url)
                        self.statusbar.push(0,url+' added to favourites')
                else:
                    #Remove server from favourites
                    favlist.remove(url)
                    self.statusbar.push(0,url+' removed from favourites')
                try:
                    f = open(favlist_path,'w')
                    for i in favlist:
                        f.write(i+'\n')
                    f.close()
                except Exception,e:
                    self.statusbar.push(0,'Failed to write favourites file: %s' % (str(e)))
            elif (event.type == gtk.gdk._2BUTTON_PRESS) or event.button == 2:
                #Set the background colour to light green on click
                #Doesn't reset the previously played row until another refresh
                self.last_played = model[path][1]
                model[path][7] ='#BFFFB8'
                self.joinGame(model[path][1])
        return True

    def menuEvent(self,widget,event):
        self.widget.popup(None, None, None, event.button, event.time)
    
    def draw_columns(self,treeview):
        log('[main] draw_columns')
        self.ren = gtk.CellRendererToggle()
        #self.ren.connect("toggled",self.serverListEvent,self.liststore)
        self.tvfav = gtk.TreeViewColumn('Fav',self.ren,active=0)
        #self.tvfav.set_clickable(True)
        self.tvfav.set_sort_column_id(0)

        rt = gtk.CellRendererText()
        self.tvurl = gtk.TreeViewColumn("URL",rt, text=1,background=7)
        self.tvurl.set_sort_column_id(1)

        rt = gtk.CellRendererText()
        self.ping = gtk.TreeViewColumn("Ping",rt, text=2,background=7)
        self.ping.set_sort_column_id(2)

        rt = gtk.CellRendererText()
        self.tvcurr = gtk.TreeViewColumn("Playing",rt, text=3,background=7)
        self.tvcurr.set_sort_column_id(3)

        rt = gtk.CellRendererText()
        self.tvmax = gtk.TreeViewColumn("Max",rt, text=4,background=7)
        self.tvmax.set_sort_column_id(4)

        rt = gtk.CellRendererText()
        self.tvname = gtk.TreeViewColumn("Name",rt, text=5,background=7)
        self.tvname.set_sort_column_id(5)

        rt = gtk.CellRendererText()
        self.tvip = gtk.TreeViewColumn("IP",rt, text=6,background=7)
        self.tvip.set_sort_column_id(6)
        for i in [self.tvfav,self.tvurl,self.ping,self.tvcurr,self.tvmax,self.tvname,self.tvip]:
            treeview.append_column(i)
        
        log('[main] Finish drawing...')
                
    def __init__(self):
        self.last_played = None
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(600,650)
        self.window.set_title("5 of Diamonds")
        self.statusbar = gtk.Statusbar()
        try:
            self.window.set_icon_from_file("diamonds.png")
        except Exception, e:
            self.statusbar.push(0,"Error: "+str(e))
        self.window.connect("delete_event",self.delete_event)
        self.window.connect("destroy",self.destroy)
        self.window.set_border_width(10)

        self.sw = gtk.ScrolledWindow()
        self.sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        #[fav,url,ping,playing,max_players,name,ip,last_played]
        self.liststore = gtk.ListStore(bool,str,int, int, int,str, str,str)
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

##        self.pathB = gtk.Button("Find Client.exe")
##        self.pathB.connect("clicked",self.pop_path,None)
        
        self.joinB = gtk.Button("Add Server")
        self.joinB.connect("clicked",self.getip,None)
        
        #stick the buttons in a frame at the bottom of the window
        #use a hbox of 3 vboxes
        # Could probably refactor this with some lists and iterations
        
        self.frame = gtk.Frame("Game Config")
        self.xresE = gtk.Entry()
        self.yresE = gtk.Entry()
        self.nameE = gtk.Entry()
        self.volE  = gtk.Entry()
        self.invert = gtk.Entry()
        self.caplim = gtk.Entry()
        self.lXres = gtk.Label("X Res")
        self.lYres = gtk.Label("Y Res")
        self.lName = gtk.Label("Name")
        self.lVolume = gtk.Label("Volume")
        self.linvert = gtk.Label("Invert Mouse")
        self.lcaplim = gtk.Label("Cap limit")
        
        self.forms = gtk.HBox()
        self.box1 = gtk.VBox(False,0)
        self.box2 = gtk.VBox(False,0)
        self.box3 = gtk.VBox(False,0)

        self.box1.pack_start(self.lXres,True,True,0)
        self.box1.pack_start(self.xresE,False,False,0)
        
        self.box1.pack_start(self.lYres,True,True,0)
        self.box1.pack_start(self.yresE,False,False,0)
        
        self.box2.pack_start(self.lName,True,True,0)
        self.box2.pack_start(self.nameE,False,False,0)
                        
        self.box2.pack_start(self.lVolume,True,True,0)
        self.box2.pack_start(self.volE,False,False,0)

        self.box3.pack_start(self.linvert,True,True,0)
        self.box3.pack_start(self.invert,False,False,0)
                        
        self.box3.pack_start(self.lcaplim,True,True,0)
        self.box3.pack_start(self.caplim,False,False,0)

        self.aboutFrame = gtk.Frame("About")
        self.abvbox = gtk.VBox(True,3)
        
        self.abtlbl = gtk.Label("5 of Diamonds\nVersion "+str(VERSION)+"\n2011\nGot bugs? Get the latest version")
        self.abtlbl.set_justify(gtk.JUSTIFY_CENTER)
        self.abvbox.pack_start(self.abtlbl)

        self.aboutFrame.add(self.abvbox)

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
        for i in [self.box1,self.box2,self.box3]:
            self.forms.pack_start(i,True,True,0)

        self.frameBox = gtk.HBox()
        self.frameBox.pack_start(self.frame,True,True,5)
        self.frameBox.pack_start(self.aboutFrame,True,True,5)
        #self.forms.pack_start(self.aboutFrame,True,True,0)
        self.frame.add(self.forms)
        self.loadConfig()
        self.vbox = gtk.VBox(False,5)
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(3)

        #removed pathB
        buttons =[self.exitB,self.refreshB,self.saveB,self.webB,self.appB,self.serverB,self.joinB]
        for i in buttons:
            self.hbox.pack_start(i,False,False,0)
            
        self.vbox.pack_start(self.hbox,False,False,0)
        self.vbox.pack_start(self.sw,True,True,0)
        self.vbox.pack_start(self.frameBox,False,False,0)
        self.vbox.pack_start(self.filterFrame,False,False,0)
        self.vbox.pack_start(self.statusbar, False, False, 0)

        # Contain everything in a single Vbox
        self.window.add(self.vbox)
        self.window.show_all()
        #Don't refresh on startup for testing purposes
        self.refresh()

    def main(self):
            gtk.main()
            
if __name__ == "__main__":
    base = Base()
    base.main()

