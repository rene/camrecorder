#!/usr/bin/env python
#-*-encoding:utf-8-*-

##
# camrecorder - Record and streaming video
# Copyright (C) 2011 Renê de Souza Pinto. 
#
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

from optparse import OptionParser
from datetime import datetime
from os import path
import sys, signal, random
import glib, gobject

try:
	import pygst
	pygst.require("0.10")
	import gst
except:
	print 'You should have GStreamer python bindings installed on your system.'
	sys.exit(1)

# Camrecorder object
class CamRecorder:

	# Default interval time to split streaming (in seconds)
	DEFAULT_INTERV_TIME = 3600

	##
	# Class Constructor
	#
	# The pipeline for this application is:
	#
	#                                          ------------   ----------   ------------   ---------   --------   ------------
	#                                       |-| videoscale |-| vfilter0 |-| theoraenc0 |-| oggmux0 |-| queue0 |-| shout2send |
	#   ---------   --------------   ----- 1|  ------------   ----------   ------------   ---------   --------   ------------
	#  | v4l2src |-| clockoverlay |-| tee |-|
	#   ---------   --------------   ----- 0|  ------------   ----------   ------------   ---------   --------   ----------
	#                                       |-| videoscale |-| vfilter1 | | theoraenc1 |-| oggmux1 |-| queue1 |-| filesink |
	#                                          ------------   ----------   ------------   ---------   --------   ----------
	#
	def __init__(self):

		self.timeformat = '%d-%m-%Y_%H:%M:%S'

		self.device   = '/dev/video0'

		self.ip       = '127.0.0.1'
		self.port     = 8000
		self.mount    = ''
		self.password = None
		self.output   = 'camrecorder-'

		# Create pipeline
		self.pipeline = gst.Pipeline('camrec-pl')

		# Elements
		self.tee    = gst.element_factory_make('tee', 'tee1')
		self.queue0 = gst.element_factory_make('queue', 'queue0')
		self.queue1 = gst.element_factory_make('queue', 'queue1')

		# Video
		self.videosrc     = gst.element_factory_make('v4l2src', 'videosrc')
		self.clockoverlay = gst.element_factory_make('clockoverlay', 'clock')
		
		# Encoders
		self.theoraenc0   = gst.element_factory_make('theoraenc', 'theora0')
		self.theoraenc1   = gst.element_factory_make('theoraenc', 'theora1')
		self.oggmux0      = gst.element_factory_make('oggmux', 'oggmux0')
		self.oggmux1      = gst.element_factory_make('oggmux', 'oggmux1')

		# Icecast streaming
		self.shout = gst.element_factory_make('shout2send', 'shout')

		# Video recorder
		self.filesink = gst.element_factory_make('filesink', 'fout')
		
		# Filters
		caps0 = gst.Caps('video/x-raw-yuv,width=512,height=384')
		self.vfilter0 = gst.element_factory_make('capsfilter', 'vfilter0')
		self.vfilter0.set_property('caps', caps0)
		
		caps1 = gst.Caps('video/x-raw-yuv,width=640,height=480')
		self.vfilter1 = gst.element_factory_make('capsfilter', 'vfilter1')
		self.vfilter1.set_property('caps', caps1)

		# Videoscale
		self.vsc0 = gst.element_factory_make('videoscale', 'vc0')
		self.vsc1 = gst.element_factory_make('videoscale', 'vc1')


		# Connect elements
		self.pipeline.add(self.videosrc, self.clockoverlay, self.tee, \
							self.vsc0, self.vfilter0, self.theoraenc0, self.oggmux0, self.queue0, self.shout, \
							self.vsc1, self.vfilter1, self.theoraenc1, self.oggmux1, self.queue1, self.filesink)

		gst.element_link_many(self.videosrc, self.clockoverlay, self.tee)
		gst.element_link_many(self.vsc0, self.vfilter0, self.theoraenc0, self.oggmux0, self.queue0, self.shout)
		gst.element_link_many(self.vsc1, self.vfilter1, self.theoraenc1, self.oggmux1, self.queue1, self.filesink)

		# Connect tee pads
		teepad0 = self.tee.get_request_pad('src0')
		teepad1 = self.tee.get_request_pad('src1')
		teepad1.link(self.vsc0.get_pad('sink'))
		teepad0.link(self.vsc1.get_pad('sink'))

		# Bus
		bus = self.pipeline.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self.cb_messages)

		# Init random
		random.seed()

		# Flag to change output file
		self.wait_change_file = False
		self.change_ready = True


	##
	# Start streaming and recording server.
	#
	# \param device Video device (i.e. /dev/video0).
	# \param ip Icecast server ip.
	# \param port Icecast server port.
	# \param mount Source client mount name.
	# \param password Icecast server password.
	# \param output Output file base name.
	#
	def start(self, device, ip, port, mount, password, output):

		self.device   = device
		self.ip       = ip
		self.port     = port
		self.mount    = mount
		self.password = password

		if output != None:
			self.output = output

		# Set element properties

		# Video source
		self.videosrc.set_property('device', device)
		
		# Clock overlay
		self.clockoverlay.set_property('halign', 'right')
		self.clockoverlay.set_property('valign', 'top')
		self.clockoverlay.set_property('shaded-background', 'true')
		self.clockoverlay.set_property('time-format', '%d/%m/%Y %H:%M:%S')
	
		# Theora enc
		self.theoraenc0.set_property('quality', 48)
		self.theoraenc1.set_property('quality', 48)
		
		# Filesink
		self.filesink.set_property('location', self.get_newfilename())

		# Shoutcast
		self.shout.set_property('ip', self.ip)
		self.shout.set_property('port', self.port)
		
		if self.password != None:
			self.shout.set_property('password', self.password)
		if self.mount != None:
			self.shout.set_property('mount', self.mount)

		# Signal handling
		signal.signal(signal.SIGALRM, self.split_stream)
		signal.alarm(self.DEFAULT_INTERV_TIME)

		# Start streaming
		self.pipeline.set_state(gst.STATE_PLAYING)

		print 'Using video device: %s' % device
		print 'Starting server:'
		print '    ip:    %s' % ip
		print '    port:  %d' % port
		print '    mount: %s' % mount

	##
	# Callback to treat streaming error messages.
	#
	def cb_messages(self, bus, message):
		
		t = message.type
		if t == gst.MESSAGE_ERROR:
			err, debug = message.parse_error()
			print "Error: %s" % err
			print debug
		elif t == gst.MESSAGE_STATE_CHANGED:
			old, new, pending = message.parse_state_changed()
			if new == gst.STATE_READY:
				if self.wait_change_file == True:
					self.change_ready = True
					self.swap_outputfile()

	##
	# Return a timestamp.
	#
	def get_timestamp(self):

		tnow = datetime.now()
		tstamp = tnow.strftime(self.timeformat)
		return tstamp

	##
	# Return new file name with timestamp, 
	# checking if there is no file with same name.
	#
	def get_newfilename(self):
		
		fname = ''
		if self.output != None:
			fname = self.output

		fname = fname + self.get_timestamp() + '.ogg'
		if path.isfile(fname):
			fname = fname + '_' + str(random.randint(0,200000)) + '.ogg'
			
		return fname

	##
	# Change output file of the stream to a new generated file.
	# \note We need to wait pipeline to change his status.
	#
	def swap_outputfile(self):

		if self.wait_change_file == False:
			self.wait_change_file = True
			self.change_ready = False
			self.pipeline.set_state(gst.STATE_READY)
		else:
			if self.change_ready == True:
				# Change location of filesink
				self.queue1.unlink(self.filesink)
				self.pipeline.remove(self.filesink)
				self.filesink.set_state(gst.STATE_NULL)
				self.filesink.set_property('location', self.get_newfilename())
				self.pipeline.add(self.filesink)
				self.queue1.link(self.filesink)

				# Start pipeline again
				self.pipeline.set_state(gst.STATE_PLAYING)
				self.wait_change_file = False
				self.change_ready = False

	##
	# Periodic function to change output file name, spliting streaming
	# in several files to avoid hudge files.
	#
	def split_stream(self, signum, frame):

		# Signal handling
		signal.alarm(self.DEFAULT_INTERV_TIME)

		# Swap output file
		state, pending, timeout = self.pipeline.get_state()
		if pending == gst.STATE_PLAYING:
			self.swap_outputfile()


##
# Quit application.
#
def quit(signum, frame):
	server.pipeline.set_state(gst.STATE_NULL)
	gobject.idle_add(server.main_loop.quit)


# main
if __name__ == '__main__':

	# Signal handling
	signal.signal(signal.SIGINT, quit)

	# Parse arguments
	parser = OptionParser()
	parser.add_option('-d', '--device', dest='device', help='Video device (i.e. /dev/video0)')
	parser.add_option('-a', '--address', dest='ip', help='IP of Icecast source server')
	parser.add_option('-p', '--port', dest='port', help='Icecast server port')
	parser.add_option('-m', '--mount', dest='mount', help='Icecast mount point')
	parser.add_option('-s', '--password', dest='password', help='Icecast password')
	parser.add_option('-o', '--output', dest='output', help='Output file base name')

	options, args = parser.parse_args()

	# Validate them
	if options.device == None:
		print 'Please, provide device file with --device option.'
		sys.exit(1)
	
	if options.ip == None:
		options.ip = '127.0.0.1'
		print 'No IP provided, using %s' % options.ip

	if options.port == None:
		port = 8000
		print 'No port provided, using default %d' % port
	else:
		port = int(options.port)

	if options.mount == None:
		options.mount = 'live.ogg'
		print 'No mount point provided, using %s' % options.mount

	server = CamRecorder()
	server.start(options.device, options.ip, port, options.mount, options.password, options.output)
	
	# Enter to GLib MainLoop
	try:
		server.main_loop = gobject.MainLoop()
		server.main_loop.run()
	except KeyboardInterrupt:
		print 'Good bye!'

