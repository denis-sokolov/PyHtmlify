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

class Error(Exception): pass
class OverwriteError(Error): pass
class WritingError(Error): pass

class Htmlifier:
	force = False
	def htmlify(self, input, output):
		if os.path.exists(output) and not self.force:
			raise OverwriteError('Destination exists and force mode is off.')
		inf = open(input)
		html = inf.read()
		inf.close()

		try:
			outf = open(output, 'w')
		except IOError:
			raise WritingError('Destination cannot be opened for writing. Check your permissions.')
		outf.write(html)
		outf.close()

def main():
	from optparse import OptionParser
	parser = OptionParser(version='%prog 1.0',
		usage='Usage: %prog [options] input output',
		description='''Htmlify squeezes all resources an HTML page needs into one big HTML file.
		http://github.com/Akral/PyHtmlify''')
	parser.add_option("-f", "--force", dest="force", default=False,
		action="store_true", help="Overwrite files.")
	(options, args) = parser.parse_args()
	if len(args) <> 2:
		parser.error('You must specify two arguments.')

	h = Htmlifier()
	h.force = options.force
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