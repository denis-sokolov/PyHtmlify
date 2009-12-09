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
from HTMLParser import HTMLParser

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

		parser = self.__Parser(os.path.dirname(input))
		parser.feed(html)
		html = parser.get()

		if self.addGpl3 == True:
			html = self.__gpl3 + html
		try:
			outf = open(output, 'w')
		except IOError:
			raise WritingError('Destination cannot be opened for writing. Check your permissions.')
		outf.write(html)
		outf.close()

	class __Parser(HTMLParser):
		def __init__(self, path):
			HTMLParser.__init__(self)
			self.path = path
			self.__data = []
			self.__uriRe = re.compile('^(((http|ftp)s?|file)://|(mailto|gopher):)', re.I)

		def get(self):
			return ''.join(self.__data)

		def reset(self, *args, **kwds):
			self.__data = []
			return HTMLParser.reset(self, *args, **kwds)

		def handle_starttag(self, tag, attrs, selfClose = False):
			attrs = dict(attrs)
			if tag == 'script' and 'src' in attrs:
				js = self.__file(attrs['src'])
				del attrs['src']
				self.__data.append('<script%s>%s</script>' % (self.__attrs(attrs), js))
			elif tag == 'link' and 'rel' in attrs and attrs['rel'] == 'stylesheet' and 'href' in attrs:
				css = self.__file(attrs['href'])
				self.__data.append('<style type="text/css">%s</style>' % css)
			else:
				if 'src' in attrs:
					attrs['src'] = self.__uriToData(attrs['src'])
				if tag == 'link' and 'href' in attrs:
					attrs['href'] = self.__uriToData(attrs['href'])

				selfClose = selfClose and ' /' or ''
				self.__data.append('<%s%s%s>' % (tag, self.__attrs(attrs), selfClose))

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

		def handle_startendtag(self, tag, attrs):
			self.handle_starttag(tag, attrs, selfClose=True)
		def handle_endtag(self, tag):
			self.__data.append('</%s>' % tag)
		def handle_data(self, data):
			self.__data.append(data)
		def handle_charref(self, name):
			self.__data.append('&#%s;' % name)
		def handle_entityref(self, name):
			self.__data.append('&%s;' % name)
		def handle_decl(self, decl):
			self.__data.append('<!%s>' % decl)
		def handle_pi(self, pi):
			self.__data.append('<?%s>' % pi)

		def __file(self, path):
			path = os.path.join(self.path, path)
			f = open(path)
			data = f.read()
			f.close()
			return data

		def __attrs(self, attrs):
			return ''.join([' %s="%s"' % (k,v) for k,v in attrs.items()])

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