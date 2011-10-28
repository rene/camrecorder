#!/usr/bin/env python

from optparse import OptionParser
import glib, gtk

try:
	import pygst
	pygst.require("0.10")
	import gst
except:
	print 'You should have GStreamer python bindings installed on your system.'
	sys.exit(1)

# Camrecorder object
class CamRecorder:

	# Status
	ST_NOT_STARTED  = 0
	ST_STREAMING    = 1
	ST_PAUSED       = 2

	##
	# Class Constructor
	#
	# The pipeline for this application is:
	#                                                                   --------   ------------
	#                                                                |-| queue0 |-| shout2send |
	#   ---------   --------------   -----------   --------   -----  |  --------   ------------
	#  | v4l2src |-| clockoverlay |-| theoraenc |-| oggmux |-| tee |-|
	#   ---------   --------------   -----------   --------   -----  |  --------   ----------
	#                                                                |-| queue1 |-| filesink |
	#                                                                   --------   ----------
	#
	def __init__(self):

		self.device   = '/dev/video0'

		self.ip       = '127.0.0.1'
		self.port     = 8000
		self.mount    = ''
		self.password = None
		
		self.status = CamRecorder.ST_NOT_STARTED

		# Create pipeline
		self.pipeline = gst.Pipeline('camrec-pl')

		# Elements
		self.tee    = gst.element_factory_make('tee', 'tee1')
		self.queue0 = gst.element_factory_make('queue', 'queue0')
		self.queue1 = gst.element_factory_make('queue', 'queue1')

		# Video
		self.videosrc     = gst.element_factory_make('v4l2src', 'videosrc')
		self.clockoverlay = gst.element_factory_make('clockoverlay', 'clock')
		self.theoraenc    = gst.element_factory_make('theoraenc', 'theora')
		self.oggmux       = gst.element_factory_make('oggmux', 'oggm')

		# Icecast streaming
		self.shout = gst.element_factory_make('shout2send', 'shout')

		# Video recorder
		self.filesink = gst.element_factory_make('filesink', 'fout')
		
		# Connect elements
		self.pipeline.add(self.videosrc, self.clockoverlay, self.theoraenc, self.oggmux, self.tee, self.queue0, self.queue1, self.filesink, self.shout)
		gst.element_link_many(self.videosrc, self.clockoverlay, self.theoraenc, self.oggmux, self.tee)
		gst.element_link_many(self.queue0, self.shout)
		gst.element_link_many(self.queue1, self.filesink)

		# Connect tee pads
		teepad0 = self.tee.get_request_pad('src0')
		teepad1 = self.tee.get_request_pad('src1')
		teepad0.link(self.queue0.get_pad('sink'))
		teepad1.link(self.queue1.get_pad('sink'))

		# Bus
		bus = self.pipeline.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self.cb_messages)



	##
	# Start streaming and recording server.
	#
	# \param device Video device (i.e. /dev/video0).
	# \param ip Icecast server ip.
	# \param port Icecast server port.
	# \param mount Source client mount name.
	# \param password Icecast server password.
	#
	def start(self, device, ip, port, mount, password):

		self.device   = device
		self.ip       = ip
		self.port     = port
		self.mount    = mount
		self.password = password

		# Set element properties

		# Video source
		self.videosrc.set_property('device', device)
		
		# Clock overlay
		self.clockoverlay.set_property('halign', 'right')
		self.clockoverlay.set_property('valign', 'top')
		self.clockoverlay.set_property('shaded-background', 'true')
		self.clockoverlay.set_property('time-format', '%d/%m/%Y %H:%M:%S')
	
		# Theora enc
		self.theoraenc.set_property('quality', 48)
		
		# Filesink
		self.filesink.set_property('location', 'teste.ogg')

		# Shoutcast
		self.shout.set_property('ip', self.ip)
		self.shout.set_property('port', self.port)
		
		if self.password != None:
			self.shout.set_property('password', self.password)
		if self.mount != None:
			self.shout.set_property('mount', self.mount)

		self.pipeline.set_state(gst.STATE_PLAYING)

		print 'Using video device: %s' % device
		print 'Starting server:'
		print '    ip:    %s' % ip
		print '    port:  %d' % port
		print '    mount: %s' % mount


	def cb_messages(self, bus, message):
		
		t = message.type
		if t == gst.MESSAGE_STATE_CHANGED:

			old, new, pending = message.parse_state_changed()

			if new == gst.STATE_PLAYING:
				print 'Playing...'
			elif new == gst.STATE_NULL:
				print 'Null'
			elif new == gst.STATE_PAUSED:
				print 'Paused'

		elif t == gst.MESSAGE_ERROR:
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
			return
		
		elif t == gst.MESSAGE_BUFFERING:
			print 'Buffering...'

		return


# main
if __name__ == '__main__':

	# Parse arguments
	parser = OptionParser()
	parser.add_option('-d', '--device', dest='device', help='Video device (i.e. /dev/video0)')
	parser.add_option('-a', '--address', dest="ip", help="IP of Icecast source server")
	parser.add_option('-p', '--port', dest="port", help="Port of Icecast")
	parser.add_option('-m', '--mount', dest="mount", help="Icecast mount point")
	parser.add_option('-s', '--password', dest="password", help="Icecast password")

	options, args = parser.parse_args()

	# Validate them
	if options.device == None:
		print 'Please, provide device file with --device option.'
		sys.exit(1)
	elif options.ip == None:
		options.ip = '127.0.0.1'
		print 'No IP provided, using %s' % options.ip

	if options.port == None:
		port = 8000
		print 'No port provided, using default %d' % port
	else:
		port = int(options.port)

	server = CamRecorder()
	server.start(options.device, options.ip, port, options.mount, options.password)

	# Enter to GLib MainLoop
	gtk.gdk.threads_init()
	try:
		gtk.main()
	except KeyboardInterrupt:
		server.pipeline.set_state(gst.STATE_NULL)
		print 'Good Bye!'

