#
# osx.py
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#
from deluge.ui.gtkui.gtkui import reactor

from deluge.log import LOG as log
from deluge.ui.client import client

import gtk, gtk.glade
import gtk_osxapplication

class OSX(object):
    def __init__(self, gtkui):
        log.debug('integrating')
        self.gtkui = gtkui
        self.osxapp = gtk_osxapplication.OSXApplication()
        self.connect()
        self.menu_bar()
        self.osxapp.ready()

    def accel_swap(self, item, group, skey, smod, dkey, dmod):
        item.remove_accelerator(group, ord(skey), smod)
        item.add_accelerator("activate", group, ord(dkey), dmod, gtk.ACCEL_VISIBLE)

    def accel_meta(self, item, group, key):
        self.accel_swap(item, group, key, gtk.gdk.CONTROL_MASK, key, gtk.gdk.META_MASK)

    def menu_bar(self):
        log.debug('menu_bar')
        window = self.gtkui.mainwindow
        glade  = window.main_glade
        menubar = glade.get_widget("menubar")
        group = gtk.accel_groups_from_object(window.window)[0]

        # NOTE: accel maps doesn't work with glade file format
        # because of libglade not setting MenuItem accel groups
        # That's why we remove / set accelerators by hand... (dirty)
        # Clean solution: migrate glades files to gtkbuilder format
        file_menu = glade.get_widget("menu_file").get_submenu()
        file_items = file_menu.get_children()
        self.accel_meta(file_items[0], group, 'o')
        self.accel_meta(file_items[1], group, 'n')
        quit_all_item = file_items[3]
        self.accel_swap(quit_all_item, group, 'q', gtk.gdk.SHIFT_MASK | gtk.gdk.CONTROL_MASK,
                                              'q', gtk.gdk.SHIFT_MASK | gtk.gdk.META_MASK)
        for item in range(2, len(file_items)): # remove quits
            file_menu.remove(file_items[item])

        menu_widget = glade.get_widget("menu_edit")
        edit_menu = menu_widget.get_submenu()
        edit_items = edit_menu.get_children()
        pref_item = edit_items[0]
        self.accel_swap(pref_item, group, 'p', gtk.gdk.CONTROL_MASK, ',', gtk.gdk.META_MASK)
        edit_menu.remove(pref_item)

        conn_item = edit_items[1]
        self.accel_meta(conn_item, group, 'm')
        edit_menu.remove(conn_item)

        menubar.remove(menu_widget)

        help_menu = glade.get_widget("menu_help").get_submenu()
        help_items = help_menu.get_children()
        about_item = help_items[4]
        help_menu.remove(about_item)
        help_menu.remove(help_items[3]) # separator

        menubar.hide()
        self.osxapp.set_menu_bar(menubar)
        # populate app menu
        self.osxapp.insert_app_menu_item(about_item, 0)
        self.osxapp.insert_app_menu_item(gtk.SeparatorMenuItem(), 1)
        self.osxapp.insert_app_menu_item(pref_item, 2)
        self.osxapp.insert_app_menu_item(conn_item, 3)
        if quit_all_item.get_visible():
            self.osxapp.insert_app_menu_item(gtk.SeparatorMenuItem(), 4)
            self.osxapp.insert_app_menu_item(quit_all_item, 5)

    def connect(self):
        self.osxapp.connect("NSApplicationOpenFile", self.open_file)
        self.osxapp.connect("NSApplicationBlockTermination", self.quit)

    # from http://sourceforge.net/mailarchive/forum.php?thread_name=AANLkTikUhZpPrg6VdXu64QBw8V1iGTXd5oZ6NCT%2BYrkv%40mail.gmail.com&forum_name=gtk-osx-users
    def open_file(self, osxapp, filename):
        # Will be raised at app launch (python opening main script)
        if filename.endswith('Deluge-bin'):
            return True

        def on_show(result):
            self.gtkui.addtorrentdialog.add_from_files([filename])
        def show():
            d = self.gtkui.addtorrentdialog.show(self.gtkui.config["focus_add_dialog"])
            d.addCallback(on_show)

        if not client.connected():
            log.debug('queuing file %s', filename)
            self.gtkui.queuedtorrents.add_to_queue([filename])
        else:
            log.debug('opening file %s', filename)
            show() # doesn't look like required anymore: gobject.idle_add(show)
        return True

    def quit(self, *args):
        log.debug('quit')
        self.gtkui.shutdown()
        reactor.stop()
        return False