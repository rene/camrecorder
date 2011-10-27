#!/usr/bin/env python
#-*-encoding:utf-8-*-

##
# radiorec - a simple program to play and record streams
# Copyright (C) 2010 Renê de Souza Pinto
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import pygtk
pygtk.require("2.0")
import gtk, gobject
import os, shutil
from radiorec import rrdb
from radiorec.classifier import classifier
from radiorec.playback import playback
from radiorec.timeout import Timeout
from radiorec.userconf import Userconf


##
# Radiorec main window class
#
class MainWin:

	##
	# MainWin constructor
	#
	def __init__(self):

		self.version = "0.1 beta"

		## User HOME dir
		try:
			homedir = os.environ.get("HOME") + "/"
		except:
			homedir = "./"

		## Check (and create) path
		rrdir = homedir + ".radiorec/"
		if not os.path.exists(rrdir):
			try:
				os.mkdir(rrdir)
			except OSError:
				print "ERROR: Radiorec user directory creation failed."

		## Check (and create) default streams list
		defaultlist = "rrlist_default.xml"
		self.rrlist_file = rrdir + "rrlist.xml"
		if not os.path.isfile(self.rrlist_file):
			try:
				shutil.copy(defaultlist, self.rrlist_file)
			except:
				pass

		## List of streams
		self.rlist = rrdb.list()
		self.rlist.read_from_file(self.rrlist_file)

		## User configurations
		self.userconf_file = rrdir + "radiorec.conf"
		self.userconf = Userconf()
		try:
			self.userconf.read_config(self.userconf_file)
		except:
			try:
				self.userconf.write_config(self.userconf_file)
			except:
				print "ERROR on read and create a new configuration file."
				print "Radiorec will use default propertites."


		## Playback object
		self.playback = playback()
		self.playback.connect("on_change_state", self.cb_pb_cg_state)
		self.playback.connect("on_change_track", self.cb_pb_cg_track)
		self.playback.connect("on_change_duration", self.cb_pb_cg_duration)
		self.playback.connect("on_buffering", self.cb_cg_buffer)
		self.playback.connect("on_error", self.cb_on_error)
		self.update_playpack_settings()

		## Timeout for change time
		self.timeout = Timeout(1, self.cb_get_time)
		self.list    = None
		
		## UI
		self.builder1 = gtk.Builder()
		self.builder2 = gtk.Builder()
		self.builder3 = gtk.Builder()
		builder = self.builder1
		builder.add_from_file("ui/radiorec-ui.glade")
		builder.connect_signals({"on_mainwin_destroy"    : self.cb_mnu_file_quit,
								  "cb_new"               : self.cb_new,
								  "cb_mnu_new"           : self.cb_new,
								  "on_bt_edit_clicked"   : self.cb_edit,
								  "on_bt_rec_toggled"    : self.cb_rec,
								  "on_mnu_file_open_activate"  : self.cb_mnu_file_open,
								  "on_mnu_file_save_activate"  : self.cb_mnu_file_save,
								  "on_mnu_pref_activate"       : self.cb_mnu_pref,
								  "on_mnu_help_about_activate" : self.cb_mnu_help_about,
								  "on_mnu_file_quit_activate"  : self.cb_mnu_file_quit})
			
		self.window = builder.get_object("mainwin")
		self.window.set_title("Radiorec")

		x, y, width, height, wstate = self.userconf.get_window_properties()

		## FIXME: Implement save state of window position and size
		self.window.set_position(gtk.WIN_POS_CENTER)

		if wstate == Userconf.WINDOW_MAXIMIZED:
			self.window.maximize()
			self.window.wstate = Userconf.WINDOW_MAXIMIZED
		else:
			self.window.wstate = Userconf.WINDOW_NORMAL

		self.window.connect("window-state-event", self.cb_win_state)
		self.window.set_icon_from_file("ui/radiorec.png")
		self.window.show_all()

		## Genres list, follow ID3v1 specification with winamp extension
		## For more information, see Appendix A at http://www.id3.org/id3v2.3.0
		self.genres_list = ['Blues', 'Classic Rock', 'Country', 'Dance', 'Disco',
			'Funk', 'Grunge', 'Hip-Hop', 'Jazz', 'Metal', 'New Age', 'Oldies',
			'Other', 'Pop', 'R&B', 'Rap', 'Reggae', 'Rock', 'Techno', 'Industrial',
			'Alternative', 'Ska', 'Death Metal', 'Pranks', 'Soundtrack', 'Euro-Techno',
			'Ambient', 'Trip-Hop', 'Vocal', 'Jazz+Funk', 'Fusion', 'Trance', 'Classical',
			'Instrumental', 'Acid', 'House', 'Game', 'Sound Clip', 'Gospel', 'Noise',
			'AlternRock', 'Bass', 'Soul', 'Punk', 'Space', 'Meditative', 'Instrumental Pop',
			'Instrumental Rock', 'Ethnic', 'Gothic', 'Darkwave', 'Techno-Industrial',
			'Electronic', 'Pop-Folk', 'Eurodance', 'Dream', 'Southern Rock', 'Comedy',
			'Cult', 'Gangsta', 'Top 40', 'Christian Rap', 'Pop/Funk', 'Jungle',
			'Native American', 'Cabaret', 'New Wave', 'Psychadelic', 'Rave', 'Showtunes',
			'Trailer', 'Lo-Fi', 'Tribal', 'Acid Punk', 'Acid Jazz', 'Polka', 'Retro',
			'Musical', 'Rock & Roll', 'Hard Rock', 'Folk', 'Folk-Rock', 'National Folk',
			'Swing', 'Fast Fusion', 'Bebob', 'Latin', 'Revival', 'Celtic', 'Bluegrass',
			'Avantgarde', 'Gothic Rock', 'Progressive Rock', 'Psychedelic Rock',
			'Symphonic Rock', 'Slow Rock', 'Big Band', 'Chorus', 'Easy Listening',
			'Acoustic', 'Humour', 'Speech', 'Chanson', 'Opera', 'Chamber Music', 'Sonata',
			'Symphony', 'Booty Bass', 'Primus', 'Porn Groove', 'Satire', 'Slow Jam', 'Club',
			'Tango', 'Samba', 'Folklore', 'Ballad', 'Power Ballad', 'Rhythmic Soul', 'Freestyle',
			'Duet', 'Punk Rock', 'Drum Solo', 'A capella', 'Euro-House', 'Dance Hall']
		
		self.gstore  = gtk.ListStore(gobject.TYPE_STRING)
		for g in self.genres_list:
			self.gstore.append([g])

		## ListTree for TreeView
		self.lstore  = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gtk.gdk.Pixbuf, gobject.TYPE_INT)
		self.listree = builder.get_object("listtree")
		self.listree.set_model(self.lstore)
		self.listree.connect("button_press_event", self.cb_listree_bpress)
		cell1   = gtk.CellRendererText()
		cell2   = gtk.CellRendererText()
		cell3   = gtk.CellRendererPixbuf()
		ltcol1  = gtk.TreeViewColumn("Name", cell1, text=0)
		ltcol2  = gtk.TreeViewColumn("Genre", cell2, text=1)
		ltcol3  = gtk.TreeViewColumn("Classification", cell3, pixbuf=2)
		ltcol1.connect("clicked", self.cb_column_click, [0])
		ltcol2.connect("clicked", self.cb_column_click, [1])
		ltcol3.connect("clicked", self.cb_column_click, [2])

		## Set appearance
		ltcol1.set_resizable(True)
		ltcol1.set_sort_column_id(0)
		ltcol1.set_sort_indicator(True)
		ltcol1.set_expand(True)

		ltcol2.set_resizable(True)
		ltcol2.set_sort_column_id(1)
		ltcol2.set_expand(True)

		ltcol3.set_fixed_width(25)
		ltcol3.set_max_width(25)
		ltcol3.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		ltcol3.set_sort_column_id(3)
		ltcol3.set_expand(True)

		self.listree.append_column(ltcol1)
		self.listree.append_column(ltcol2)
		self.listree.append_column(ltcol3)
		self.listree.set_reorderable(True)
		self.listree.set_enable_search(True)

		## Menus
		self.list_popup = gtk.Menu()
		mnu_proper = gtk.ImageMenuItem(gtk.STOCK_PROPERTIES)
		mnu_remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
		mnu_proper.show()
		mnu_remove.show()
		self.list_popup.append(mnu_remove)
		self.list_popup.append(mnu_proper)
		mnu_proper.connect("activate", self.cb_ltpopup_proper)
		mnu_remove.connect("activate", self.cb_ltpopup_remove)
		self.listree.connect("button_press_event", self.cb_list_popup_menu)
		self.mnu_pref = builder.get_object("mnu_pref")

		## Other objects
		self.statusbar = builder.get_object("statusbar")
		self.statusbar.push(self.statusbar.get_context_id("app"), "Ready.")
		self.progbar   = gtk.ProgressBar()
		self.progbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
		self.progbar.set_text("Buffering...")

		self.lbl_track = builder.get_object("lbl_track")
		self.lbl_time  = builder.get_object("lbl_time")
		self.hstime    = builder.get_object("hstime")

		self.lbl_track.set_text("No stream.")

		self.bt_play = builder.get_object("bt_play")
		self.bt_stop = builder.get_object("bt_stop")
		self.bt_rec  = builder.get_object("bt_rec")

		self.bt_play.connect("clicked", self.cb_play)
		self.bt_stop.connect("clicked", self.cb_stop)

		self.bt_stop.set_sensitive(False)
		self.bt_rec.set_sensitive(False)


		col, order = self.userconf.get_sort()

		if col == 0:
			ltcol1.emit("clicked")
		elif col == 1:
			ltcol2.emit("clicked")
		elif col == 2:
			ltcol3.emit("clicked")

		if order == Userconf.SORT_ASCENDING:
			if col == 0:
				ltcol1.emit("clicked")
			elif col == 1:
				ltcol2.emit("clicked")
			elif col == 2:
				ltcol3.emit("clicked")
		
		self.userconf.set_sort(col, order)

	##
	# Populate stations list
	# @param list
	#
	def populate_list(self, list):

		self.list = list
		self.lstore.clear()
		for k, st in self.list.iteritems():
			clf = classifier()
			clf.set_value(int(st.classify))
			self.lstore.append([st.name, self.genres_list[int(st.genre)], clf.get_pixbuf(), int(st.classify)])

	##
	# Update playback settings with user settings
	#
	def	update_playpack_settings(self):
		
		self.playback.set_filename(self.userconf.get_filename())
		self.playback.set_format(self.userconf.get_format())
		self.playback.set_recopt(self.userconf.get_recopt())


	##
	# Open window for new station
	#
	def cb_new(self, widget):

		builder = self.builder2
		builder.add_from_file("ui/radiowin-ui.glade")
		radiowin = builder.get_object("radiowin")
		builder.connect_signals({"on_bt_radiowin_ok_clicked"    : self.cb_btradiowin_ok,
								   "on_bt_radiowin_cancel_clicked": self.cb_btradiowin_cancel,
								   "on_bt_radiowin_clear_clicked" : self.cb_btradiowin_clear}, radiowin)
		radiowin.set_position(gtk.WIN_POS_CENTER)
		radiowin.set_title("New station")
		icon = radiowin.render_icon(gtk.STOCK_NEW, gtk.ICON_SIZE_BUTTON)
		radiowin.set_icon(icon)
		combobox = builder.get_object("cb_radiowin_g")

		cell3 = gtk.CellRendererText()
		combobox.pack_start(cell3, True)
		combobox.add_attribute(cell3, 'text', 0)  
		combobox.set_model(self.gstore)
		combobox.set_active(0)

		radiowin.classify = classifier("classifier")
		hbox = self.builder2.get_object("hbox_class")
		hbox.pack_end(radiowin.classify.get_child())

		radiowin.set_transient_for(self.window)
		radiowin.set_modal(True)
		radiowin.show_all()
		radiowin.classify.set_enable(True)

	##
	# Open window for edit station
	#
	def cb_edit(self, widget):

		builder = self.builder2
		builder.add_from_file("ui/radiowin-ui.glade")
		radiowin = builder.get_object("radiowin")
		builder.connect_signals({"on_bt_radiowin_ok_clicked"    : self.cb_btradiowin_ok,
								   "on_bt_radiowin_cancel_clicked": self.cb_btradiowin_cancel,
								   "on_bt_radiowin_clear_clicked" : self.cb_btradiowin_clear}, radiowin)
		radiowin.set_position(gtk.WIN_POS_CENTER)
		radiowin.set_title("Edit station")
		icon = radiowin.render_icon(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON)
		radiowin.set_icon(icon)
		combobox = builder.get_object("cb_radiowin_g")

		cell3 = gtk.CellRendererText()
		combobox.pack_start(cell3, True)
		combobox.add_attribute(cell3, 'text', 0)  
		combobox.set_model(self.gstore)

		radiowin.classify = classifier("classifier")
		hbox = builder.get_object("hbox_class")
		hbox.pack_end(radiowin.classify.get_child())

		# Load values
		selection  = self.listree.get_selection()
		model,iter = selection.get_selected()

		if iter != None:
			rname = model.get_value(iter, 0)
			try:
				dict  = self.rlist.get_list()
				radio = dict[rname]

				txtname  = builder.get_object("txt_radiowin_name")
				txturl   = builder.get_object("txt_radiowin_url")
				txtdesc  = builder.get_object("txt_desc")
	
				txtname.set_text(radio.name)
				txtname.set_editable(False)
				txturl.set_text(radio.url)
				combobox.set_active(int(radio.genre))
				
				buffdesc = txtdesc.get_buffer()
				if radio.description != None:
					buffdesc.set_text(radio.description)

				radiowin.classify.set_value(int(radio.classify))

			except:
				return
		else:
			return

		# Show window
		radiowin.set_transient_for(self.window)
		radiowin.set_modal(True)
		radiowin.show_all()
		radiowin.classify.set_enable(True)


	##
	# Clear new station window fields
	#
	def cb_btradiowin_clear(self, widget, userdata):

		builder  = self.builder2
		txtname  = builder.get_object("txt_radiowin_name")
		txturl   = builder.get_object("txt_radiowin_url")
		txtdesc  = builder.get_object("txt_desc")
 		combobox = builder.get_object("cb_radiowin_g")
	
		if txtname.get_editable() == True:
			txtname.set_text('')
		txturl.set_text('')
		combobox.set_active(0)

		buffdesc = txtdesc.get_buffer()
		buffdesc.set_text('')

		userdata.classify.set_value(0)


	##
	# Close new station windows
	#
	def cb_btradiowin_cancel(self, widget, userdata):

		userdata.destroy()

	##
	# Add new station
	#
	def cb_btradiowin_ok(self, widget, userdata):

		builder  = self.builder2
		txtname  = builder.get_object("txt_radiowin_name")
		txturl   = builder.get_object("txt_radiowin_url")
		txtdesc  = builder.get_object("txt_desc")
		combobox = builder.get_object("cb_radiowin_g")

		name = txtname.get_text()
		url  = txturl.get_text()
		
		buffdesc = txtdesc.get_buffer()
		desc     = buffdesc.get_text(buffdesc.get_iter_at_offset(0),
									 buffdesc.get_iter_at_offset(buffdesc.get_char_count()))

 
 		# Validate
 		if len(name) == 0 or len(url) == 0:
			dia = gtk.Dialog(userdata.get_title(), userdata.get_toplevel(),
					gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
					(gtk.STOCK_OK, gtk.RESPONSE_OK))
			wicon = gtk.image_new_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
			hbox  = gtk.HBox()
			hbox.pack_start(wicon)

			if len(name) == 0:
				hbox.pack_start(gtk.Label('The station name is empty!'))
			else:
				hbox.pack_start(gtk.Label('The URL is empty!'))
			
			dia.vbox.pack_start(hbox)
			picon = dia.render_icon(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_MENU)
			dia.set_icon(picon)
			dia.show_all()
			dia.run()
			dia.destroy()
			return

		if userdata.get_title() == "New station":
			# Add new Station
			try:
				self.list[name]

				dia = gtk.Dialog(userdata.get_title(), userdata.get_toplevel(),
						gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
						(gtk.STOCK_OK, gtk.RESPONSE_OK))
				wicon = gtk.image_new_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
				hbox  = gtk.HBox()
				hbox.pack_start(wicon)
				hbox.pack_start(gtk.Label('The new station already exist!'))
				dia.vbox.pack_start(hbox)
				picon = dia.render_icon(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_MENU)
				dia.set_icon(picon)
				dia.show_all()
				dia.run()
				dia.destroy()
			except:
				radio = rrdb.station()
				radio.name = name
				radio.url  = url
				radio.description = desc
				radio.classify    = userdata.classify.get_value()
				radio.genre       = combobox.get_active()

				self.list[radio.name] = radio

				self.lstore.append([radio.name, self.genres_list[int(radio.genre)], userdata.classify.get_pixbuf(), int(radio.classify)])
		else:
			# Edit Station
			selection  = self.listree.get_selection()
			model,iter = selection.get_selected()

			if iter != None:
				rname = model.get_value(iter, 0)
				try:
					dict  = self.rlist.get_list()
					radio = dict[rname]

					radio.url  		  = url
					radio.description = desc
					radio.classify    = userdata.classify.get_value()
					radio.genre       = combobox.get_active()

					clf = classifier()
					clf.set_value(int(radio.classify))
					model.set_value(iter, 1, self.genres_list[radio.genre])
					model.set_value(iter, 2, clf.get_pixbuf())
					model.set_value(iter, 3, int(radio.classify))

				except:
					pass

		userdata.destroy()


	##
	# popup menu of list
	#
	def cb_list_popup_menu(self, treeview, event):

		if event.button == 3:
			x = int(event.x)
			y = int(event.y)
			time = event.time
			pthinfo = treeview.get_path_at_pos(x, y)
			if pthinfo is not None:
				path, col, cellx, celly = pthinfo
				treeview.grab_focus()
				treeview.set_cursor(path, col, 0)
				self.list_popup.popup(None, None, None, event.button, time)
			return True

	##
	# properties menu callback
	#
	def cb_ltpopup_proper(self, menuitem, userdata=None):
		selection  = self.listree.get_selection()
		model,iter = selection.get_selected()

		if iter != None:
			rname = model.get_value(iter, 0)
			try:
				dict  = self.rlist.get_list()
				radio = dict[rname]
			except:
				print 'internal error'
				return False
	
			# Load properties window
			builder = gtk.Builder()
			builder.add_from_file("ui/properties-ui.glade")
			propwin = builder.get_object("propwin")
			builder.connect_signals({"on_bt_propwin_ok_clicked" : self.cb_propwin_ok}, propwin)

			txtname    = builder.get_object("txt_propwin_name")
			txturl     = builder.get_object("txt_propwin_url")
			txtdesc    = builder.get_object("txt_desc")
			lbl_genre  = builder.get_object("lbl_genre")
			hbox_class = builder.get_object("hbox_class")
	
			txtname.set_text(radio.name)
			txturl.set_text(radio.url)
			lbl_genre.set_label(self.genres_list[int(radio.genre)])
				
			buffdesc = txtdesc.get_buffer()
			if radio.description != None:
				buffdesc.set_text(radio.description)

			propwin.classify = classifier("propclf")
			hbox_class.pack_start(propwin.classify.get_child())
			hbox_class.reorder_child(propwin.classify.get_child(), 1)
			propwin.classify.set_value(int(radio.classify))

			# Show window
			propwin.set_position(gtk.WIN_POS_CENTER)
			propwin.set_transient_for(self.window)
			propwin.set_modal(True)
			propwin.show_all()
			propwin.classify.set_enable(False)
	

	##
	# remove
	#
	def cb_ltpopup_remove(self, menuitem, userdata=None):
		selection  = self.listree.get_selection()
		model,iter = selection.get_selected()

		if iter != None:
			rname = model.get_value(iter, 0)
			try:
				dict  = self.rlist.get_list()
				radio = dict[rname]
			except:
				print 'internal error'
				return False
	
		dia = gtk.Dialog("Remove Station", None,
						gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
						(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, gtk.RESPONSE_NO))
		wicon = gtk.image_new_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
		hbox  = gtk.HBox()
		hbox.pack_start(wicon)
		hbox.pack_start(gtk.Label("This will remove " + radio.name + " from the list. Are you sure?"))
		dia.vbox.pack_start(hbox)
		picon = dia.render_icon(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_MENU)
		dia.set_icon(picon)
		dia.show_all()
		response = dia.run()
		dia.destroy()

		if response == gtk.RESPONSE_YES:
			del dict[rname]
			model.remove(iter)

	##
	# callback for close window
	#
	def cb_propwin_ok(self, widget, propwin):
		propwin.destroy()


	##
	# File->open callback
	#
	def cb_mnu_file_open(self, menuitem, userdata=None):
		dia = gtk.FileChooserDialog("Open list", None, gtk.FILE_CHOOSER_ACTION_OPEN,
				(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
		
		# xml filter
		filter = gtk.FileFilter()
		filter.set_name("XML Files")
		filter.add_mime_type("text/xml")
		filter.add_pattern("*.xml")
		dia.add_filter(filter)

		# 'all files' filter
		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		dia.add_filter(filter)

		response = dia.run()

		if response == gtk.RESPONSE_ACCEPT:
			filename = dia.get_filename()
			dia.destroy()

			new_list = rrdb.list()
			if new_list.read_from_file(filename):
				self.rlist = new_list
				self.populate_list(self.rlist.get_list())
			else:
				dia   = gtk.Dialog("Error", None,
							gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
							(gtk.STOCK_OK, gtk.RESPONSE_OK))
				wicon = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_DIALOG)
				hbox  = gtk.HBox()
				hbox.pack_start(wicon)
				hbox.pack_start(gtk.Label("Error on open " + filename + " file."))
				dia.vbox.pack_start(hbox)
				picon = dia.render_icon(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU)
				dia.set_icon(picon)
				dia.show_all()
				dia.run()
				dia.destroy()
		else:
			dia.destroy()


	##
	# File->save callback
	#
	def cb_mnu_file_save(self, menuitem, userdata=None):
		
		dia = gtk.FileChooserDialog("Save list", None, gtk.FILE_CHOOSER_ACTION_SAVE,
				(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
		
		# xml filter
		filter = gtk.FileFilter()
		filter.set_name("XML Files")
		filter.add_mime_type("text/xml")
		filter.add_pattern("*.xml")
		dia.add_filter(filter)

		# 'all files' filter
		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		dia.add_filter(filter)

		response = dia.run()
	
		if response == gtk.RESPONSE_ACCEPT:
			filename = dia.get_filename()
			dia.destroy()
			try:
				self.rlist.write_to_file(filename)
			except:
				dia   = gtk.Dialog("Error", None,
							gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
							(gtk.STOCK_OK, gtk.RESPONSE_OK))
				wicon = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_DIALOG)
				hbox  = gtk.HBox()
				hbox.pack_start(wicon)
				hbox.pack_start(gtk.Label("Error on save " + filename +" file."))
				dia.vbox.pack_start(hbox)
				picon = dia.render_icon(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU)
				dia.set_icon(picon)
				dia.show_all()
				dia.run()
				dia.destroy()
		else:
			dia.destroy()


	##
	# Help->about callback
	#
	def cb_mnu_help_about(self, menuitem, userdata=None):

		logo = gtk.image_new_from_file("ui/radiorec.png")
		aboutwin = gtk.AboutDialog()
		aboutwin.set_name("Radiorec")
		aboutwin.set_logo(logo.get_pixbuf())
		icon = aboutwin.render_icon(gtk.STOCK_ABOUT, gtk.ICON_SIZE_MENU)
		aboutwin.set_icon(icon)
		aboutwin.set_version(self.version)
		aboutwin.set_authors(["Renê de Souza Pinto <rene@renesp.com.br>"])
		aboutwin.set_comments("A simple program to play and record audio streams")
		aboutwin.set_website("http://radio-rec.sourceforge.net")
		aboutwin.set_copyright("Copyright (c) 2010 Renê S. Pinto")

		try:
			license_file = open("ui/license")
			license_ls   = license_file.readlines()
			license_str  = ""
			
			for line in license_ls:
				license_str += line

			aboutwin.set_license(license_str)
			aboutwin.set_wrap_license(True)

			license_file.close()
		except:
			pass

		aboutwin.run()
		aboutwin.destroy()


	##
	# Preferences callback
	#
	def cb_mnu_pref(self, menuitem, userdata=None):

		builder = self.builder3
		builder.add_from_file("ui/preferences-ui.glade")
		prefwin = builder.get_object("prefwin")
		builder.connect_signals({"on_bt_prefwin_apply_clicked"  : self.cb_prefwin_apply,
		   					     "on_bt_prefwin_cancel_clicked" : self.cb_btradiowin_cancel}, prefwin)
		prefwin.set_position(gtk.WIN_POS_CENTER)
		prefwin.set_title("Preferences")
		icon     = prefwin.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_BUTTON)
		prefwin.set_icon(icon)
		
		# Check recorder plugins
		rpstore  = gtk.ListStore(gobject.TYPE_STRING)
		rplugins = self.playback.get_rec_plugins()
		index    = 0
		dicp     = {}
		for p in rplugins:
			if p == self.playback.FORMAT_OGG:
				rpstore.append(["Vorbis audio encoder (*.OGG)"])
				dicp[self.playback.FORMAT_OGG] = index
				index += 1
			elif p == self.playback.FORMAT_MP3:
				rpstore.append(["L.A.M.E. mp3 encoder (*.MP3)"])
				dicp[self.playback.FORMAT_MP3] = index
				index += 1

		try:
			act = dicp[self.userconf.get_format()]
		except:
			act = 0
		
		prefwin.dicp = dicp

		combobox = builder.get_object("cb_prefwin_fmt")
		cell3 = gtk.CellRendererText()
		combobox.pack_start(cell3, True)
		combobox.add_attribute(cell3, 'text', 0)
		combobox.set_model(rpstore)
		combobox.set_active(act)

		## Load values
		txt_filename = builder.get_object("txt_filename")
		txt_filename.set_text(self.userconf.get_filename())

		recopt = self.userconf.get_recopt()
		if recopt == playback.REC_IMMEDIATALY:
			rb_recopt = builder.get_object("rb_prefwin_im")
			rb_recopt.set_active(True)
		elif recopt == playback.REC_ON_NEXT:
			rb_recopt = builder.get_object("rb_prefwin_next")
			rb_recopt.set_active(True)

		## Show window
		prefwin.set_transient_for(self.window)
		prefwin.set_modal(True)
		prefwin.show_all()

	##
	# preferences ok button callback
	#
	def cb_prefwin_apply(self, widget, userdata=None):
	
		builder = self.builder3

		txt_filename = builder.get_object("txt_filename")
		self.userconf.set_filename(txt_filename.get_text())

		combobox = builder.get_object("cb_prefwin_fmt")
		index = combobox.get_active()

		try:
			dicp_keys   = userdata.dicp.keys()
			dicp_values = userdata.dicp.values()
			pos = dicp_values.index(index)
			self.userconf.set_format(dicp_keys[pos])
		except:
			pass

		recopt = builder.get_object("rb_prefwin_im")
		if recopt.get_active():
			self.userconf.set_recopt(self.playback.REC_IMMEDIATALY)
		else:
			self.userconf.set_recopt(self.playback.REC_ON_NEXT)

		self.update_playpack_settings()
		userdata.destroy()
	
	
	##
	# Quit callback
	#
	def cb_mnu_file_quit(self, menuitem, userdata=None):
		self.quit()

	##
	# do quit operations
	#
	def quit(self):
		self.timeout.stop()
		
		try:
			self.rlist.write_to_file(self.rrlist_file)
		except:
			print "ERROR: Could not write streams list file!"


		## FIXME: Implement save state of window position and size
		width, height = self.window.get_size_request()
		px = -1
		py = -1
		self.userconf.set_window_properties(px, py, width, height, self.window.wstate)
		
		try:
			self.userconf.write_config(self.userconf_file)
		except:
			print "ERROR: Could not write configuration file!"

		gtk.main_quit()


	##
	# Window state event callback
	#
	def cb_win_state(self, widget, event, userdata=None):

		if event.type == gtk.gdk.WINDOW_STATE:
			if (event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED):
				if (event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED):
					self.window.wstate = Userconf.WINDOW_MAXIMIZED
				else:
					self.window.wstate = Userconf.WINDOW_NORMAL


	##
	# Tree list view mouse event callback
	#
	def cb_listree_bpress(self, widget, event):
		if event.button == 1:
			if event.type == gtk.gdk._2BUTTON_PRESS:
				# Double click
				self.cb_play(None, None)

	##
	# Columns of Tree list callback
	#
	def cb_column_click(self, widget, userdata=None):

		if userdata is not None:
			col = userdata[0]
			c, uorder = self.userconf.get_sort()

			if uorder == Userconf.SORT_ASCENDING:
				order = Userconf.SORT_DESCENDING
			else:
				order = Userconf.SORT_ASCENDING

			self.userconf.set_sort(col, order)


	##
	# Play button callback
	#
	def cb_play(self, widget, userdata=None):
		selection  = self.listree.get_selection()
		model,iter = selection.get_selected()

		if iter != None:
			rname = model.get_value(iter, 0)
			try:
				dict  = self.rlist.get_list()
				radio = dict[rname]
			except:
				print 'internal error'
				return False

			if self.playback.get_state() == playback.STATE_PLAYING:
				self.cb_stop(self.bt_stop)

			self.bt_play.set_sensitive(False)
			self.bt_stop.set_sensitive(True)
			self.statusbar.push(self.statusbar.get_context_id("playback"), "Conecting: " + radio.url)
			self.playback.set_uri(radio.url)
			self.playback.set_state(playback.STATE_PLAYING)

	##
	# Stop button callback
	#
	def cb_stop(self, widget, userdata=None):

		self.playback.set_state(playback.STATE_STOPPED)

	##
	# Record button callback
	#
	def cb_rec(self, widget, userdata=None):

		if widget.get_active():
			self.playback.set_recorder_state(self.playback.STATE_RECORDER_ON)
		else:
			self.playback.set_recorder_state(self.playback.STATE_RECORDER_OFF)


	##
	# Playback callbacks
	##

	##
	# Error callback
	#
	def cb_on_error(self, pb, errors, userdata=None):

		gtk.gdk.threads_enter()
		
		dia = gtk.Dialog("Error", None,
							gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
							(gtk.STOCK_OK, gtk.RESPONSE_OK))
		wicon  = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_DIALOG)
		msgerr = gtk.Label(errors[1])
		msgerr.set_line_wrap(True)
		hbox   = gtk.HBox()
		hbox.pack_start(wicon)
		hbox.pack_start(msgerr)
		dia.vbox.pack_start(hbox)
		picon = dia.render_icon(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU)
		dia.set_icon(picon)
		dia.show_all()
		dia.run()
		dia.destroy()

		gtk.gdk.threads_leave()

	##
	# Change state callback
	#
	def cb_pb_cg_state(self, pb, userdata=None):

		gtk.gdk.threads_enter()

		st = self.playback.get_state()

		if st == playback.STATE_PLAYING:
			self.bt_play.set_sensitive(False)
			self.bt_stop.set_sensitive(True)
			self.bt_rec.set_sensitive(True)
			self.mnu_pref.set_sensitive(False)

			self.timeout.start()
			self.statusbar.push(self.statusbar.get_context_id("playback"), "Playing: " + self.playback.get_uri())

		elif st == playback.STATE_PAUSED:
			self.bt_play.set_sensitive(False)
			self.bt_stop.set_sensitive(True)
			self.bt_rec.set_sensitive(True)
			self.mnu_pref.set_sensitive(False)

			self.statusbar.push(self.statusbar.get_context_id("playback"), "Wait...")

		elif st == playback.STATE_STOPPED:
			self.bt_play.set_sensitive(True)
			self.bt_stop.set_sensitive(False)
			self.bt_rec.set_sensitive(False)
			self.bt_rec.set_active(False)
			self.mnu_pref.set_sensitive(True)

			self.timeout.stop()
			self.statusbar.push(self.statusbar.get_context_id("playback"), "Ready.")

			if self.progbar.get_parent() is not None:
				gtk.Container.remove(self.statusbar, self.progbar)

			self.lbl_track.set_text("No stream.")
			self.lbl_time.set_text("00:00")

		gtk.gdk.threads_leave()


	##
	# Change buffer callback
	# Note that this callback has the 
	#
	def cb_cg_buffer(self, pb, percent, userdata=None):

		if percent >= 100:
			gtk.Container.remove(self.statusbar, self.progbar)
		else:
			if self.progbar.get_parent() == None:
				self.statusbar.pack_end(self.progbar, False, True, 0)
				self.progbar.show_all()

		## Avoid progress bar to get crazy going back/foward many times
		pbfrac  = self.progbar.get_fraction()
		buffrac = percent / 100.0 
		if abs(buffrac - pbfrac) >= 0.08:
			self.progbar.set_fraction(buffrac)

	##
	# Change track callback
	#
	def cb_pb_cg_track(self, pb, userdata=None):

		title = self.playback.get_title()
		if title is not None:
			self.lbl_track.set_text(title)
		else:
			self.lbl_track.set_text("Untitled")

	##
	# Change duration callback
	#
	def cb_pb_cg_duration(self, pb, userdata=None):

		duration = self.playback.get_duration()
		if duration > 0:
			self.hstime.set_range(0, duration)

	##
	# Get time of playback
	#
	def cb_get_time(self, userdata=None):
		
		gtk.gdk.threads_enter()					
		self.lbl_time.set_text(self.playback.get_time_str())
		self.hstime.set_value(self.playback.get_time())
		gtk.gdk.threads_leave()
		return True


##
# main
#
if __name__ == "__main__":
	mwin = MainWin()
	mwin.populate_list(mwin.rlist.get_list())
	gtk.gdk.threads_init()
	gtk.main()

