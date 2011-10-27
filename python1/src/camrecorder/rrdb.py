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

from xml.etree.ElementTree import Element,ElementTree

##
# radiorec database utilities
#

##
# list class: Store radio stations information
#
class list:

	##
	# list constructor
	#
	def __init__(self):

		self.list = {}


	##
	# Read list from xml file
	# @param filename File to read
	#
	def read_from_file(self, filename):

		try:
			tree = ElementTree(file=filename)
			root = tree.getroot()
		except:
			self.show_error("Invalid XML file!")
			return False

		if root.tag == 'rrlist':
			stations = root.getchildren()
			if len(stations) > 0:
				for s in stations:
					if s.tag == 'station':
						radio          = station()
						radio.genre    = s.attrib['genre']
						radio.classify = s.attrib['classify']
						tags           = 0

						rprop = s.getchildren()
						for p in rprop:
							if p.tag == 'name':
								radio.name = p.text
								tags += 1
							elif p.tag == 'url':
								radio.url = p.text
								tags += 1
							elif p.tag == 'description':
								radio.description = p.text
								tags += 1
							else:
								self.show_error("Unknown property of station")
								return False

							if tags == 3:
								self.list[radio.name] = radio
					else:
						self.show_error("Wrong tag in XML file")
						return False
			else:
				self.show_error("The list are empty!")
				return False

		else:
			self.show_error("Wrong tag in XML file.")
			return False

		return True


	##
	# Write list to file
	# @param filename File to write
	# @return True if file was written, False otherwise
	#
	def write_to_file(self, filename):

		root = Element("rrlist")

		for k, s in self.list.iteritems():

			station = Element("station", genre=str(s.genre), classify=str(s.classify))

			name      = Element("name")
			name.text = s.name
			
			url       = Element("url")
			url.text  = s.url

			desc      = Element("description")
			desc.text = s.description

			station.append(name)
			station.append(url)
			station.append(desc)
			root.append(station)
		
		ElementTree(root).write(filename,"UTF-8")


	##
	# Return the list
	# @return List
	#
	def get_list(self):

		return self.list


	##
	# Show error message
	# @param msg Error message
	#
	def show_error(self, msg):

		print "ERROR: " + msg



##
# station class
# Specify a Radio stream
#
class station:

	##
	# Radio constructor
	#
	def __init__(self):

		self.name 		 = ""
		self.url  		 = ""
		self.description = ""
		self.genre       = 0
		self.classify    = 0


	def tostr(self):
		return "NAME:" + self.name + "|URL:" + self.url + "|DESC:" + self.description + "|GENRE:" + self.genre + "|CLASS:" + self.classify


