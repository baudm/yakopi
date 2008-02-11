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
from array import array
from xml.dom import minidom


__all__ = [
    'Message',
    'Archive',
    'kopete_parse',
    'pidgin_parse',
    'yahoo_decode'
    ]


class Message(object):

    def __init__(self, inbound, day, time, content):
        self.inbound = inbound
        self.day = day
        self.time = time
        self.content = content


class Archive(object):

    def __init__(self):
        self.myself = None
        self.peer = None
        self.year = None
        self.month = None
        self.messages = []

    def to_kopete(self, outfile=None):
        """Output the archive contents as a Kopete history file.

        @param outfile: file to write contents to

        Returns the file contents if outfile is None, else returns None.
        """
        doc = minidom.Document()
        # DOCTYPE
        doctype = minidom.DocumentType("Kopete-History")
        doc.appendChild(doctype)
        # kopete-history
        history = doc.createElement("kopete-history")
        history.setAttribute('version', '0.9')
        doc.appendChild(history)
        # head
        head = doc.createElement("head")
        history.appendChild(head)
        # date
        date = doc.createElement("date")
        date.setAttribute('month', str(self.month))
        date.setAttribute('year', str(self.year))
        head.appendChild(date)
        # contact: myself
        myself = doc.createElement("contact")
        myself.setAttribute('contactId', self.myself)
        myself.setAttribute('type', 'myself')
        head.appendChild(myself)
        # contact: peer
        peer = doc.createElement("contact")
        peer.setAttribute('contactId', self.peer)
        head.appendChild(peer)
        # msg
        for msg in self.messages:
            msg_elem = doc.createElement('msg')
            from_ = self.peer if msg.inbound else self.myself
            in_ = '1' if msg.inbound else '0'
            time = "%d %s" % (msg.day, ":".join(map(str, msg.time)))
            msg_elem.setAttribute('nick', from_)
            msg_elem.setAttribute('in', in_)
            msg_elem.setAttribute('from', from_)
            msg_elem.setAttribute('time', time)
            text = doc.createTextNode(msg.content)
            msg_elem.appendChild(text)
            history.appendChild(msg_elem)
        if outfile is not None:
            file = open(outfile, 'w')
            file.writelines(doc.toxml().\
                replace('<?xml version="1.0" ?>\n', '').\
                replace('<h', '\n <h').\
                replace('<d', '\n  <d').\
                replace('<c', '\n  <c').\
                replace('</h', '\n </h').\
                replace('<m', '\n <m').\
                replace('</k', '\n</k'))
            file.close()
        else:
            return doc.toxml().\
                replace('<?xml version="1.0" ?>\n', '').\
                replace('<h', '\n <h').\
                replace('<d', '\n  <d').\
                replace('<c', '\n  <c').\
                replace('</h', '\n </h').\
                replace('<m', '\n <m').\
                replace('</k', '\n</k')

    def to_pidgin(self, outfile=None):
        """Output the archive contents as a Pidgin log file.

        @param outfile: file to write contents to

        Returns the file contents if outfile is None, else returns None.
        """
        lines = []
        msg = self.messages[0]
        line = "Conversation with %s at %d-%02d-%02d %02d:%02d:%02d on %s (yahoo)" % \
            (self.peer, self.year, self.month, msg.day, msg.time[0], msg.time[1], msg.time[2], self.myself)
        lines.append(line)
        for msg in self.messages:
            line = "(%02d:%02d:%02d) %s: %s" % (msg.time[0], msg.time[1], msg.time[2], self.peer if msg.inbound else self.myself, msg.content)
            lines.append(line)
        if outfile is not None:
            file = open(outfile, 'w')
            file.writelines("\n".join(lines))
            file.close()
        else:
            return "\n".join(lines)

    def to_yahoo(self, outfile=None):
        """Output the archive contents as a Yahoo! Messenger archive file.

        This method is not yet implemented.

        @param outfile: file to write contents to

        Returns the file contents if outfile is None, else returns None.
        """
        raise NotImplementedError("to_yahoo() method not yet implemented")


def kopete_parse(path):
    """Parse a Kopete history file

    @param path: path to history file

    Returns an instance of Archive which contains the data.
    """
    archive = Archive()
    doc = minidom.parse(path)

    for contact in doc.getElementsByTagName('contact'):
        if contact.getAttribute('type') == 'myself':
            myself = contact.getAttribute('contactId')
        else:
            peer = contact.getAttribute('contactId')
    archive.myself = str(myself)
    archive.peer = str(peer)

    date = doc.getElementsByTagName('date')[0]
    archive.month = int(date.getAttribute('month'))
    archive.year = int(date.getAttribute('year'))

    for msg in doc.getElementsByTagName('msg'):
        inbound = True if msg.getAttribute('in') == '1' else False
        content = str(msg.childNodes[0].wholeText)
        day, time = msg.getAttribute('time').split()
        time = tuple(map(int, time.split(':')))
        message = Message(inbound, int(day), time, content)
        archive.messages.append(message)
    return archive


def pidgin_parse(log_files):
    """Parse a list of Pidgin log files

    @param log_files: list of log files

    Returns an instance of Archive which contains the data.
    """
    archive = Archive()
    for filename in log_files:
        file = open(filename, 'r')
        for line in file:
            if line.startswith('('):
                time, sender, content = line.split(' ', 2)
                if not sender.endswith(':'):
                    continue
                time = tuple(map(int, time.lstrip('(').rstrip(')').split(':')))
                inbound = True if sender.startswith(archive.peer) else False
                msg = Message(inbound, day, time, content.rstrip())
                archive.messages.append(msg)
            elif line.startswith('Conversation'):
                data = line.split()
                archive.myself = data[7]
                archive.peer = data[2]
                archive.year, archive.month, day = map(int, data[4].split('-'))
        file.close()
    return archive


def yahoo_decode(path):
    """Decode a Yahoo! Messenger archive file

    @param path: full path to archive file

    Returns an instance of Archive which contains the data.
    """
    #
    # TODO: look out for 'Buzz!'

    months = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }

    archive = Archive()
    ps = path.split(os.sep)

    encrypt_id = ps[ps.index('Profiles') + 1]
    archive.peer = ps[ps.index('Messages') + 1]
    archive.myself = ps[ps.index(archive.peer) + 1].split('-')[1].rstrip('.dat')

    readint = array('l') # 32-bit signed int
    readbyte = array('b') # 1 byte (8-bit int)

    file = open(path, 'rb')
    readint.fromfile(file, 5)
    timestamp = readint[0]
    # Clear readint
    map(readint.remove, readint.tolist())
    datetime = time.ctime(timestamp).split()
    # month
    archive.month = months[datetime[1]]
    # year
    archive.year = int(datetime[4])
    while file:
        try:
            readint.fromfile(file, 4)
        except EOFError:
            break
        timestamp, unknown, user, datalength = readint.tolist()
        inbound = True if user else False
        # get day, time
        day, time_ = time.ctime(timestamp).split()[2:4]
        time_ = map(int, time_.split(':'))
        readbyte.fromfile(file, datalength)
        line = []
        idx = 0
        # decode message
        for i in range(datalength):
            line.append(chr(readbyte[i] ^ ord(encrypt_id[idx])))
            idx += 1
            if idx == len(encrypt_id):
                idx = 0
        msg = Message(inbound, int(day), time_, "".join(line))
        archive.messages.append(msg)
        # read terminator
        readint.fromfile(file, 1)
        # Clear the arrays
        map(readint.remove, readint.tolist())
        map(readbyte.remove, readbyte.tolist())
    file.close()
    return archive
