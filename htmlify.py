#!/usr/bin/env python
# encoding: utf-8
#
#       htmlify.py
#
#       Copyright 2009 Denis <denis@denis-desktop>
#
#       This program is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
	Htmlify squeezes all resources an HTML page needs into one big
	HTML file.
	http://github.com/Akral/PyHtmlify
'''

import os
import re
import base64
import mimetypes

from pymins.HtmlMinifier import HtmlMinifier
from pymins.CssMinifier import CssMinifier
from pymins.JavascriptMinifier import JavascriptMinifier

class Error(Exception): pass
class OverwriteError(Error): pass
class WritingError(Error): pass
class MimeError(Error): pass
class EncodingError(Error): pass

class Htmlifier:
	force = False
	addGpl3 = True
	__gpl3 = '''<!--
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
-->
'''

	def htmlify(self, input, output):
		if os.path.exists(output) and not self.force:
			raise OverwriteError('Destination exists and force mode is off.')
		inf = open(input)
		html = inf.read()
		inf.close()

		html = HtmlMinifier(html).minify().get()

		parser = self.__Parser(os.path.dirname(input))
		html = parser.feed(html)

		if self.addGpl3 == True:
			html = self.__gpl3 + html
		try:
			outf = open(output, 'w')
		except IOError:
			raise WritingError('Destination cannot be opened for writing. Check your permissions.')
		outf.write(html)
		outf.close()

	class __Parser(object):
		def __init__(self, path):
			self.path = path
			self.__uriRe = re.compile('^(((http|ftp)s?|file)://|(mailto|gopher):)', re.I)
			
		def feed(self, html):
			for scr in re.finditer(r'\<link [^>]*rel=[\'"]?stylesheet[^>]*>', html):
				orig = scr.group(0)
				path = re.search(r'href=[\'"]*([^ ]+)[\'"]', orig).group(1)
				css = CssMinifier(self.__file(path)).minify().get()
				html = html.replace(orig, '<style type="text/css">%s</style>' % css)
			for scr in re.finditer(r'\<script [^>]*src=[\'"]*([^ >\'"]+)[^>]*>', html):
				orig = scr.group(0)
				path = scr.group(1)
				js = JavascriptMinifier(self.__file(path)).minify().get()
				html = html.replace(orig, '<script type="text/javascript">%s</script>' % js)
			# @TODO:
			# Handle images
			# Handle other resources with src or href
			# Handle other resources in CSS data
			# Correctify regexes to account for pairing quotes
			return html
				
		def __uriToData(self, uri):
			if self.__uriRe.match(uri):
				return uri
			path = os.path.join(self.path, uri)
			if not os.path.exists(path) or not os.path.isfile(path):
				return uri
			f = open(path)
			data = f.read()
			f.close()
			data = base64.b64encode(data)
			mime, encoding = mimetypes.guess_type(path, False)
			if not mime:
				raise MimeError('Cannot guess MIME type of file "%s". Give it a better name.' % path)
			if encoding:
				raise EncodingError('File "%s" appears to be encoded. I can\'t work with encoded files. Yet.' % path)
			return 'data:%s;base64,%s' % (mime, data)

		def __file(self, path):
			path = os.path.join(self.path, path)
			f = open(path)
			data = f.read()
			f.close()
			return data

def main():
	from optparse import OptionParser
	parser = OptionParser(version='%prog 1.0',
		usage='Usage: %prog [options] input output',
		description='''Htmlify squeezes all resources an HTML page needs into one big HTML file.
		http://github.com/Akral/PyHtmlify''')
	parser.add_option("-f", "--force", dest="force", default=False,
		action="store_true", help="Overwrite files.")
	parser.add_option("-g", "--addgpl3", dest="addgpl3", default=False,
		action="store_true", help="Add GPLv3 license on top of the output.")
	(options, args) = parser.parse_args()
	if len(args) <> 2:
		parser.error('You must specify two arguments.')

	h = Htmlifier()
	h.force = options.force
	h.addGpl3 = options.addgpl3
	try:
		h.htmlify(input=args[0], output=args[1])
	except OverwriteError:
		parser.error('%s exists. Use -f to overwrite.' % args[1])
		return 1
	except Error:
		import sys
		print 'Fatal error. %s' % sys.exc_info()[1]
		return 5

	return 0

if __name__ == '__main__':
	main()