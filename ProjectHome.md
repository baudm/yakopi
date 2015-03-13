YaKoPi is a pure Python module for reading and writing (and effectively, converting) Yahoo! message archives of Yahoo! Messenger (r), Kopete (rw), and Pidgin (rw).

```
>>> import yakopi
>>> # Parse a Kopete log file
>>> kop = yakopi.kopete_parse('/home/konqi/.kde/share/apps/kopete/logs/\
... YahooProtocol/konqi/katie.200802.xml')
>>> kop.to_kopete() # return the content as a Kopete log file (XML)
>>> # save the content as a Pidgin log file
>>> kop.to_pidgin(outdir='/tmp') # saved as 2008-02-<day>.<time>.txt
>>> # Parse a Pidgin log file (same with gaim_parse)
>>> pid = yakopi.pidgin_parse(['/home/konqi/.purple/logs/yahoo/konqi/\
... katie/2008-02-11.223426.txt',
... '/home/konqi/.purple/logs/yahoo/konqi/katie/2008-02-14.152312.txt'])
>>> pid.to_kopete(outdir='/tmp') # saved as katie.200802.xml
>>> # Decode a Y!M message archive file
>>> ym = yakopi.yahoo_decode(['C:\\Program Files\\Yahoo!\\Messenger\\Profiles\\\
... konqi\\Archive\\Messages\\katie\\20080211-konqi.dat'])
>>> # or you can do it like this:
>>> ym = yakopi.yahoo_decode(['/path/to/archive.dat'],
... user_id='konqi', buddy_nick='katie')
>>> ym.to_kopete() # output as Kopete log
>>> ym.to_pidgin() # output as Pidgin log
```