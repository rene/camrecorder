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

import gobject
from threading import RLock

##
# Class Timeout
# Implement a class for timeout function
#
class Timeout:

	##
	# Timeout constructor
	# @param time The time interval to execute function
	# @param func The function to be executed
	# @param arg  Argument to the function
	#
	def __init__(self, timer, func, arg=None):

		self.timer = timer
		self.func  = func
		self.arg   = arg
		self.clock = None
		self.lock  = RLock()
		self.source_id = None

	def start(self):
		self.lock.acquire(True)
		if self.source_id == None:
			self.source_id = gobject.timeout_add(self.timer * 1000, self.func, self.arg)
		self.lock.release()

	def stop(self):
		self.lock.acquire(True)
		if self.source_id is not None:
			gobject.source_remove(self.source_id)
		self.source_id = None
		self.lock.release()

