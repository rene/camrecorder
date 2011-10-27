#!/usr/bin/env python

import sys
from optparse import OptionParser

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


	def __init__(self):

		self.device   = '/dev/video0'

		self.ip       = '127.0.0.1'
		self.port     = 8000
		self.mount    = ''
		self.password = None
		
		self.status = ST_NOT_STARTED

		self.pipeline = gst.Pipeline('camrec-pl')


	def start(self, ip, port, mount, password):
		print 'Starting server:'
		print '    ip:    %s' % ip
		print '    port:  %d' % port
		print '    mount: %s' % mount

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
	server.start(options.ip, port, options.mount, options.password)

