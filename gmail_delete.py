#!/usr/bin/env python2.7
#
# Archive and delete old gmail
#
#  Copyright (c) 2011 Chris Deutsch <cdeutsch@ispeakdeutsch.com>
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
#

import os
import imaplib
import email
import mailbox
import datetime
import argparse
import getpass

class GmailArchiver:
	username = ''
	password = ''
	hostname = 'imap.gmail.com'
	mbox_filename = 'archive.mbox'
	delete_p = False
	
	#
	# Command line support
	#
	def run(self):
		parser = argparse.ArgumentParser(description='Archive old gmail mail.')
		parser.add_argument('--username', nargs=1, default=None, help='username')
		parser.add_argument('--password', nargs=1, default=None, help='password')
		parser.add_argument('--days', nargs=1, type=int, default=None, help='Mail older than n days will be archived')
		parser.add_argument('--date', nargs=1, default=None, help='Mail before DD-MMM-YYYY (eg 10-Apr-2010) will be archived')
		parser.add_argument('--delete', default=False, help='Delete?')
		args = parser.parse_args()
		
		date = None
		
		if args.username != None:
			self.username = args.username[0]
		
		if args.password != None:
			self.password = args.password[0]
		else:
			self.password = getpass.getpass("Gmail password:")
		
		num_days=int(args.days[0])
		
		if args.days != None:
			d = datetime.datetime.now() - datetime.timedelta(days=num_days)
			date = d.strftime('%d-%b-%Y')
			
		if args.date != None:
			date = args.date[0]
		
		if date == None:
			raise "You must specify either --days or --date"
		
		if args.delete:
			self.delete_p = True			
			
		self.archive(date)
	
	#
	# Perform the archival
	#
	def archive(self,date):
		c = imaplib.IMAP4_SSL(self.hostname)
		c.debug = 1
		c.login(self.username, self.password)
		c.select('INBOX')
		
		t, [ids] = c.search(None, 'BEFORE', date)
		
		mbox = mailbox.mbox(self.mbox_filename)
		mbox.lock()

		for i in ids.split():
			print "getting %s" % i
			t, msg_data = c.fetch(i, '(RFC822)')
			for response_part in msg_data:
				if isinstance(response_part, tuple):
					msg = email.message_from_string(response_part[1])
					mbox.add(msg)
						
					if self.delete_p:
						print "deleting %s" % i
						t, response = c.store(i, '+FLAGS', r'(\Deleted)')
		
		mbox.flush()
		mbox.unlock()
		
		if self.delete_p:
			typ, response = c.expunge()
	
if __name__ == '__main__':
	a = GmailArchiver()
	a.run()
