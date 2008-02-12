# $Id$
#
# yakopi - Yahoo! Messenger/Kopete/Pidgin Archives Converter
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
import time
import datetime
from array import array
from xml.dom import minidom


__all__ = [
    'Message',
    'Archive',
    'kopete_parse',
    'gaim_parse',
    'pidgin_parse',
    'yahoo_decode'
    ]


class Message(object):

    __slots__ = ['inbound', 'day', 'time', 'content']

    def __init__(self, inbound, day, time, content):
        self.inbound = inbound
        self.day = day
        self.time = time
        self.content = content

    def __repr__(self):
        content = self.content[:20]
        return "<%s%s>" % (content, '...' if content != self.content else '')


class Archive(object):

    def __init__(self):
        self.myself = None
        self.peer = None
        self.year = None
        self.month = None
        self.messages = []

    def __repr__(self):
        return "<Conversation of %s with %s>" % (self.myself, self.peer)

    def to_kopete(self, outdir=None):
        """Output the archive contents as a Kopete history file.

        @param outdir: directory to write the output to

        Returns the file contents if outdir is None, else returns None.
        """
        doc = minidom.Document()
        # DOCTYPE
        doctype = minidom.DocumentType('Kopete-History')
        doc.appendChild(doctype)
        # kopete-history
        history = doc.createElement('kopete-history')
        history.setAttribute('version', '0.9')
        doc.appendChild(history)
        # head
        head = doc.createElement('head')
        history.appendChild(head)
        # date
        date = doc.createElement('date')
        date.setAttribute('month', str(self.month))
        date.setAttribute('year', str(self.year))
        head.appendChild(date)
        # contact: myself
        myself = doc.createElement('contact')
        myself.setAttribute('contactId', self.myself)
        myself.setAttribute('type', 'myself')
        head.appendChild(myself)
        # contact: peer
        peer = doc.createElement('contact')
        peer.setAttribute('contactId', self.peer)
        head.appendChild(peer)
        # msg
        for message in self.messages:
            msg = doc.createElement('msg')
            from_ = self.peer if message.inbound else self.myself
            in_ = '1' if message.inbound else '0'
            time = "%d %s" % (message.day, ":".join(map(str, message.time)))
            msg.setAttribute('nick', from_)
            msg.setAttribute('in', in_)
            msg.setAttribute('from', from_)
            msg.setAttribute('time', time)
            content = doc.createTextNode(message.content)
            msg.appendChild(content)
            history.appendChild(msg)

        xml = doc.toxml().replace('<?xml version="1.0" ?>\n', '').\
            replace('<h', '\n <h').replace('<d', '\n  <d').\
            replace('<c', '\n  <c').replace('</h', '\n </h').\
            replace('<m', '\n <m').replace('</k', '\n</k')

        if outdir is not None:
            fname = "%s.%d%02d.xml" % (self.peer, self.year, self.month)
            path = os.path.join(outdir, fname)
            outfile = open(path, 'w')
            outfile.writelines(xml)
            outfile.close()
        else:
            return xml

    def to_pidgin(self, outdir=None):
        """Output the archive contents as a Pidgin log file.

        @param outdir: directory to write the output to

        Returns the file contents if outdir is None, else returns None.
        """
        msg = self.messages[0]
        datetime_ = datetime.datetime(self.year, self.month, msg.day, *msg.time)
        lines = []
        line = "Conversation with %s at %s on %s (yahoo)" % (self.peer, datetime_.strftime('%A, %d %B, %Y %I:%M:%S %p'), self.myself)
        lines.append(line)
        for msg in self.messages:
            time_str = datetime.time(*msg.time).strftime('%I:%M:%S')
            line = "(%s) %s: %s" % (time_str, self.peer if msg.inbound else self.myself, msg.content)
            lines.append(line)
        if outdir is not None:
            msg = self.messages[0]
            fname = datetime_.strftime('%Y-%m-%d.%H%M%S.txt')
            path = os.path.join(outdir, fname)
            outfile = open(path, 'w')
            outfile.writelines("\n".join(lines))
            outfile.close()
        else:
            return "\n".join(lines)

    def to_yahoo(self, outdir=None):
        """Output the archive contents as a Yahoo! Messenger archive file.

        This method is not yet implemented.

        @param outdir: directory to write the output to

        Returns the file contents if outdir is None, else returns None.
        """
        raise NotImplementedError("to_yahoo() method not yet implemented")


def kopete_parse(path):
    """Parse a Kopete history file

    @param path: path to history file

    Returns an instance of Archive which contains the data.
    """
    archive = Archive()
    doc = minidom.parse(path)
    # Get contact info.
    for contact in doc.getElementsByTagName('contact'):
        if contact.getAttribute('type') == 'myself':
            myself = contact.getAttribute('contactId')
        else:
            peer = contact.getAttribute('contactId')
    archive.myself = str(myself)
    archive.peer = str(peer)
    # Get month and year info.
    date = doc.getElementsByTagName('date')[0]
    archive.month = int(date.getAttribute('month'))
    archive.year = int(date.getAttribute('year'))
    # Get message info.
    for msg in doc.getElementsByTagName('msg'):
        inbound = True if msg.getAttribute('in') == '1' else False
        content = str(msg.childNodes[0].wholeText)
        day, time = msg.getAttribute('time').split()
        time = tuple(map(int, time.split(':')))
        message = Message(inbound, int(day), time, content)
        archive.messages.append(message)
    return archive


def gaim_parse(files):
    """Parse a list of Pidgin log files

    @param files: list of log files

    Returns an instance of Archive which contains the data.
    """
    archive = Archive()
    for filename in files:
        infile = open(filename, 'r')
        data = infile.readline().split()
        archive.myself = data[7]
        archive.peer = data[2]
        archive.year, archive.month, day = map(int, data[4].split('-'))
        for line in infile:
            if line.startswith('('):
                time, sender, content = line.split(' ', 2)
                if not sender.endswith(':'):
                    continue
                time = tuple(map(int, time.lstrip('(').rstrip(')').split(':')))
                inbound = True if sender.startswith(archive.peer) else False
                msg = Message(inbound, day, time, content.rstrip())
                archive.messages.append(msg)
        infile.close()
    return archive


def pidgin_parse(files):
    """Parse a list of Pidgin log files

    @param files: list of log files

    Returns an instance of Archive which contains the data.
    """

    months = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
        }

    archive = Archive()
    for filename in files:
        infile = open(filename, 'r')
        data = infile.readline().split()
        archive.myself = data[12]
        archive.peer = data[2]
        day, month, year, time_, ampm, tzone = data[5:11]
        day, archive.year = map(int, (day, year))
        archive.month = months[month.rstrip(',')]
        for line in infile:
            if line.startswith('('):
                time_, u, tzone, sender, content = line.split(' ', 4)
                if not sender.endswith(':'):
                    continue
                time_ = time.strptime("".join([time_.lstrip('('), ampm]), '%I:%M:%S%p')[3:6]
                inbound = True if sender.startswith(archive.peer) else False
                msg = Message(inbound, day, time_, content.rstrip())
                archive.messages.append(msg)
        infile.close()
    return archive


def yahoo_decode(files):
    """Decode a Yahoo! Messenger archive file

    @param files: list of archive files (full path)

    Returns an instance of Archive which contains the data.
    """
    #
    # TODO: look out for 'Buzz!'

    months = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }

    archive = Archive()

    for path in files:
        ps = path.split(os.sep)
        # Extract info based on path.
        encrypt_id = ps[ps.index('Profiles') + 1]
        archive.peer = ps[ps.index('Messages') + 1]
        archive.myself = ps[ps.index(archive.peer, ps.index('Messages')) + 1].split('-')[1].rstrip('.dat')
        infile = open(path, 'rb')
        while infile:
            # Initialize the 'data readers'.
            readint = array('l') # 32-bit signed int
            readbyte = array('b') # 1 byte (8-bit int)
            try:
                readint.fromfile(infile, 4)
            except EOFError:
                break
            timestamp, unknown, user, msglength = readint.tolist()
            # Get message direction.
            inbound = True if user else False
            # Get the date and time info.
            month, day, time_, year = time.ctime(timestamp).split()[1:]
            day = int(day)
            time_ = tuple(map(int, time_.split(':')))
            if archive.month is None:
                archive.month = months[month]
                archive.year = int(year)
            # Read the message content.
            readbyte.fromfile(infile, msglength)
            idx = 0
            content = []
            # Decode the message.
            for byte in readbyte:
                if byte >= 0:
                    content.append(chr(byte ^ ord(encrypt_id[idx])))
                idx += 1
                if idx == len(encrypt_id):
                    idx = 0
            msg = Message(inbound, day, time_, "".join(content))
            archive.messages.append(msg)
            # Read message terminator.
            readint.fromfile(infile, 1)
        infile.close()
    return archive
