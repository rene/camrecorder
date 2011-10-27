#
#-*-encoding:utf-8-*-

##
# radiorec 
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

import os
from xml.etree.ElementTree import Element,ElementTree
from playback import playback

##
# Class to handle user configuration
#
class Userconf:

	WINDOW_NORMAL    = 0
	WINDOW_MAXIMIZED = 1
	SORT_ASCENDING   = 10
	SORT_DESCENDING  = 11

	def __init__(self):

		self.filename   = ""
		self.format     = playback.FORMAT_OGG
		self.recopt     = playback.REC_ON_NEXT
		self.win_pos_x  = -1
		self.win_pos_y  = -1
		self.win_width  = -1
		self.win_height = -1
		self.win_state  = Userconf.WINDOW_NORMAL
		self.sort_col   = 0
		self.sort_order = Userconf.SORT_ASCENDING

		try:
			self.filename = os.environ['HOME'] + "/Radiorec_Music/%t"
		except:
			self.filename = "./Radiorec_Music/%t"


	##
	# Read configuration from file
	# @param filename Configuration file
	#
	def read_config(self, filename):

		tree = ElementTree(file=filename)
		root = tree.getroot()
		
		if root.tag == "radiorecconf":
			conf = root.getchildren()

			if len(conf) > 0:
				for cf in conf:
					if cf.tag == "filename":
						self.filename = cf.text
					elif cf.tag == "format":
						self.format = int(cf.text)
					elif cf.tag == "recopt":
						self.recopt = int(cf.text)
					elif cf.tag == "sort":
						self.sort_col = int(cf.text)
						try:
							self.sort_order = int(cf.attrib['order'])
						except:
							print "ERROR: Invalid attribute"
					elif cf.tag == "window":
						self.win_state = int(cf.text)
						try:
							self.win_pos_x 	= int(cf.attrib['x'])
							self.win_pos_y  = int(cf.attrib['y'])
							self.win_width  = int(cf.attrib['width'])
							self.win_height = int(cf.attrib['height'])
						except:
							print "ERROR: Invalid attribute"
					else:
						print "ERROR: Invalid TAG in xml file!"
			else:
				print "ERROR: No configuration found!"
				return False
		else:
			print "ERROR: Invalid TAG in xml file!"
			return False


	##
	# Write configuration to file
	# @param filename Configuration file
	#
	def write_config(self, filename):

		root = Element("radiorecconf")

		fname       = Element("filename")
		fname.text  = self.filename

		fmt         = Element("format")
		fmt.text    = str(self.format)

		recopt      = Element("recopt")
		recopt.text = str(self.recopt)

		sort        = Element("sort", order=str(self.sort_order))
		sort.text   = str(self.sort_col)

		window      = Element("window", width=str(self.win_width), height=str(self.win_height), x=str(self.win_pos_x), y=str(self.win_pos_y))
		window.text = str(self.win_state)

		root.append(fname)
		root.append(fmt)
		root.append(recopt)
		root.append(sort)
		root.append(window)

		ElementTree(root).write(filename, "UTF-8")


	##
	# set and get methods
	#
	def set_filename(self, filename):
		
		if filename == None:
			return False
		else:
			self.filename = filename
			return True

	def set_format(self, fmt):

		if fmt != playback.FORMAT_OGG and fmt != playback.FORMAT_MP3:
			return False
		else:
			self.format = fmt
			return True

	def set_recopt(self, recopt):

		recopts = [playback.REC_IMMEDIATALY, playback.REC_ON_NEXT]
		try:
			recopts.index(recopt)
			self.recopt = recopt
			return True
		except:
			return False

	def set_sort(self, col, order):

		if order == Userconf.SORT_ASCENDING or order == Userconf.SORT_DESCENDING:
			self.sort_col = col
			self.sort_order = order
			return True
		else:
			return False

	def set_window_properties(self, x, y, width, height, state):
		
		if state == Userconf.WINDOW_NORMAL or state == Userconf.WINDOW_MAXIMIZED:
			self.win_pos_x  = x
			self.win_pos_y  = y
			self.win_width  = width
			self.win_height = height
			self.win_state  = state
			return True
		else:
			return False


	def get_filename(self):
		return self.filename

	def get_format(self):
		return self.format

	def get_recopt(self):
		return self.recopt

	##
	# @return [col, order]
	#
	def get_sort(self):
		return [self.sort_col, self.sort_order]
	
	##
	# @return [x, y, width, height, state] window properties
	#
	def get_window_properties(self):
		return [self.win_pos_x, self.win_pos_y, self.win_width, self.win_height, self.win_state]

