# -*- coding: utf-8 -*-
# $Id$
#
# YaKoPi - Yahoo! Messenger/Kopete/Pidgin Archives Converter
# Copyright (C) 2008-2009  Darwin M. Bautista
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
import codecs
from datetime import datetime
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


class ParserError(Exception):
    """Raised for all parsing-related errors"""


class Message(object):

    __slots__ = ['inbound', 'datetime', 'content']

    def __init__(self, inbound, datetime, content):
        self.inbound = inbound
        self.datetime = datetime
        self.content = content

    def __repr__(self):
        content = self.content[:20]
        return "<%s%s>" % (content, '...' if content != self.content else '')


class Archive(object):

    def __init__(self):
        self.user_id = None
        self.user_nick = None
        self.buddy_nick = None
        self.messages = []

    def __repr__(self):
        return "<Conversation of %s with %s>" % (self.user_id, self.buddy_nick)

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
        year, month = self.messages[0].datetime[:2]
        date.setAttribute('month', str(month))
        date.setAttribute('year', str(year))
        head.appendChild(date)
        # contact: user
        user = doc.createElement('contact')
        user.setAttribute('contactId', self.user_id)
        user.setAttribute('type', 'myself')
        head.appendChild(user)
        # contact: buddy
        buddy = doc.createElement('contact')
        buddy.setAttribute('contactId', self.buddy_nick)
        head.appendChild(buddy)
        # msg
        for message in self.messages:
            msg = doc.createElement('msg')
            from_ = self.buddy_nick if message.inbound else self.user_id
            in_ = '1' if message.inbound else '0'
            time_ = "%d %d:%d:%d" % message.datetime[2:]
            msg.setAttribute('nick', from_)
            msg.setAttribute('in', in_)
            msg.setAttribute('from', from_)
            msg.setAttribute('time', time_)
            content = doc.createTextNode(message.content)
            msg.appendChild(content)
            history.appendChild(msg)

        xml = doc.toprettyxml(indent=' ', encoding='utf-8').\
            replace('<?xml version="1.0" ?>\n', '').\
            replace('">', '" >').replace('/>', ' />').\
            replace(' >\n  ', ' >').replace('\n </msg>', '</msg>')
        doc.unlink()

        if outdir is not None:
            fname = "%s.%d%02d.xml" % (self.buddy_nick, year, month)
            path = os.path.join(outdir, fname)
            outfile = codecs.open(path, 'w', 'utf-8')
            outfile.writelines(xml)
            outfile.close()
        else:
            return xml

    def to_pidgin(self, outdir=None):
        """Output the archive contents as a Pidgin log file.

        @param outdir: directory to write the output to

        Returns the file contents if outdir is None, else returns None.
        """
        datetime_ = datetime(*self.messages[0].datetime)
        lines = []
        line = "Conversation with %s at %s on %s (yahoo)" % (self.buddy_nick, datetime_.strftime('%A, %d %B, %Y %I:%M:%S %p'), self.user_id)
        lines.append(line)
        for msg in self.messages:
            time_str = datetime(*msg.datetime).strftime('%I:%M:%S')
            line = "(%s) %s: %s" % (time_str, self.buddy_nick if msg.inbound else self.user_id, msg.content)
            lines.append(line)
        if outdir is not None:
            fname = datetime_.strftime('%Y-%m-%d.%H%M%S.txt')
            path = os.path.join(outdir, fname)
            outfile = codecs.open(path, 'w', 'utf-8')
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
            archive.user_id = contact.getAttribute('contactId')
        else:
            archive.buddy_nick = contact.getAttribute('contactId')
    # Get month and year info.
    date = doc.getElementsByTagName('date')[0]
    month = int(date.getAttribute('month').encode('utf-8'))
    year = int(date.getAttribute('year').encode('utf-8'))
    # Get message info.
    # TODO: buzz = 'Buzz!!'
    for msg in doc.getElementsByTagName('msg'):
        try:
            content = msg.childNodes[0].wholeText
        except IndexError:
            continue
        inbound = (True if msg.getAttribute('in') == u'1' else False)
        day, time_ = msg.getAttribute('time').encode('utf-8').split()
        time_ = tuple(map(int, time_.split(':')))
        message = Message(inbound, (year, month, int(day))+time_, content)
        archive.messages.append(message)
    return archive


def gaim_parse(files):
    """Parse a list of Gaim log files

    @param files: list of log files

    Returns an instance of Archive which contains the data.
    """
    archive = Archive()

    for filename in files:
        infile = codecs.open(filename, 'r', 'utf-8')
        data = infile.readline().split()
        archive.user_id = data[7]
        archive.buddy_nick = data[2]
        date = tuple(map(int, data[4].split('-')))
        # TODO: look out for 'Buzz!'
        for line in infile:
            if line.startswith('('):
                time_, sender, content = line.split(' ', 2)
                if not sender.endswith(':'):
                    continue
                time_ = tuple(map(int, time_.lstrip('(').rstrip(')').split(':')))
                inbound = True if sender.startswith(archive.buddy_nick) else False
                msg = Message(inbound, date+time_, content.rstrip())
                archive.messages.append(msg)
        infile.close()
    return archive


def pidgin_parse(files):
    """Parse a list of Pidgin log files

    @param files: list of log files

    Returns an instance of Archive which contains the data.
    """
    archive = Archive()

    for filename in files:
        infile = codecs.open(filename, 'r', 'utf-8')
        data = infile.readline().split()
        archive.user_id = data[12]
        archive.buddy_nick = data[2]
        ampm = data[9]
        date = time.strptime("".join(data[5:8]), '%d%B,%Y')[:3]
        # TODO: look out for 'Buzz!'
        for line in infile:
            if line.startswith('('):
                time_, emptystr, tzone, sender, content = line.split(' ', 4)
                if not sender.endswith(':'):
                    continue
                time_ = time.strptime("".join([time_, ampm]), '(%I:%M:%S%p')[3:6]
                inbound = True if sender.startswith(archive.buddy_nick) else False
                msg = Message(inbound, date+time_, content.rstrip())
                archive.messages.append(msg)
        infile.close()
    return archive


def yahoo_decode(files, user_id='', buddy_nick=''):
    """Decode a Yahoo! Messenger archive file

    @param files: list of archive files (full path)
    @param user_id='': ID of the user (if empty, extract from path)
    @param buddy_nick='': nickname of the buddy (if empty, extract from path)

    Returns an instance of Archive which contains the data.
    """
    archive = Archive()

    for path in files:
        ps = path.split(os.sep)
        # Extract user_id based on path.
        if not user_id:
            try:
                archive.user_id = user_id = ps[-4]
            except IndexError:
                raise ParserError("user_id not specified and can't be extracted from the path.")
        else:
            archive.user_id = user_id
        # Extract buddy_nick based on path.
        if not buddy_nick:
            try:
                archive.buddy_nick = ps[-2]
            except IndexError:
                raise ParserError("buddy_nick not specified and can't be extracted from the path.")
        else:
            archive.buddy_nick = buddy_nick
        # Extract user_nick based on path.
        archive.user_nick = ps[-1][9:-4]
        if not archive.user_nick:
            archive.user_nick = user_id

        infile = open(path, 'rb')
        # TODO: look out for 'Buzz!'
        while True:
            # container for 32-bit signed int
            readint = array('i')
            try:
                readint.fromfile(infile, 4)
            except EOFError:
                break
            timestamp, blank, inbound, msglength = readint
            # A message separator/break:
            # TODO: Mark this as a message separator (useful for Pidgin output).
            if not msglength:
                # Read message terminator.
                readint.fromfile(infile, 1)
                continue
            # Get message direction.
            inbound = bool(inbound)
            # Get the date and time info.
            datetime_ = time.localtime(timestamp)[:6]
            # container for 8-bit signed char (int)
            readbyte = array('b')
            # Read the message content.
            readbyte.fromfile(infile, msglength)
            content = []
            # Decode the message.
            for i in range(msglength):
                try:
                    decoded = chr(readbyte[i] ^ ord(user_id[i % len(user_id)]))
                except ValueError:
                    continue
                else:
                    content.append(decoded)
            msg = Message(inbound, datetime_, u''.join(content))
            archive.messages.append(msg)
            # Read message terminator.
            readint.fromfile(infile, 1)
        infile.close()
    return archive
