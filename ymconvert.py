#!/usr/bin/env python
#
# Part of YaKoPi - Yahoo! Messenger/Kopete/Pidgin Archives Converter
# Copyright (C) 2008  Darwin M. Bautista
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

import os
from optparse import OptionParser

import yakopi

__version__ = "$Revision$"

# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560
# Fastest without order preserving
def uniq(alist):
    set = {}
    map(set.__setitem__, alist, [])
    return set.keys()


def main():
    ver = "".join(['%prog ', __version__])
    parser = OptionParser(version=ver, conflict_handler='resolve')
    # Add options
    parser.add_option('-k', '--kopete', action='store_const', const='kopete',
        dest='format', help='use Kopete log file format')
    parser.add_option('-p', '--pidgin', action='store_const', const='pidgin',
        dest='format', help='use Pidgin log file format')
    parser.add_option('-o', '--outdir', dest='outdir', metavar='DIR',
        default=os.getcwd(), help='output directory')

    options, args = parser.parse_args()
    if not args:
        parser.error('no files to convert')
    args.sort()
    monthly = uniq([os.path.basename(path)[:6] for path in args])

    for month in monthly:
        files = [path for path in args if os.path.basename(path).startswith(month)]
        try:
            archive = yakopi.yahoo_decode(files)
        except yakopi.ParserError, msg:
            parser.error(msg)
        if options.format == 'kopete':
            archive.to_kopete(options.outdir)
        elif options.format == 'pidgin':
            archive.to_pidgin(options.outdir)
        else:
            parser.error('format not specified')


if __name__ == "__main__":
    main()
