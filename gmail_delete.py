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
	folder   = 'INBOX'
	mbox_filename = 'archive.mbox'
	delete_p = False
	
	#
	# Command line support
	#
	def run(self):
		parser = argparse.ArgumentParser(description='Archive old gmail mail.')
		parser.add_argument('--username', nargs=1, default=None, help='username')
		parser.add_argument('--password', nargs=1, default=None, help='password')
		parser.add_argument('--purge', default=False, help='Purge mode. Delete everything and do not archive.')
		parser.add_argument('--days', nargs=1, type=int, default=None, help='Mail older than n days will be archived')
		parser.add_argument('--date', nargs=1, default=None, help='Mail before DD-MMM-YYYY (eg 10-Apr-2010) will be archived')
		parser.add_argument('--delete', default=False, help='Delete?')
		parser.add_argument('--folder', default='INBOX', help='IMAP folder')
		parser.add_argument('--mbox', default='archive.mbox', help='file to save mail to')
		args = parser.parse_args()
		
		action = None
		date = None
		
		self.folder = args.folder
		self.mbox_filename = args.mbox

		if args.purge:
			action = "purge"
		else:
			action = "archive"
			
		if args.username != None:
			self.username = args.username[0]
		
		if args.password != None:
			self.password = args.password[0]
		else:
			self.password = getpass.getpass("Gmail password:")
		
		if args.delete or args.purge:
			self.delete_p = True			
		
		if action == "archive":
			num_days=int(args.days[0])
		
			if args.days != None:
				d = datetime.datetime.now() - datetime.timedelta(days=num_days)
				date = d.strftime('%d-%b-%Y')
			
			if args.date != None:
				date = args.date[0]
		
			if date == None:
				raise "You must specify either --days or --date"
		elif action == "purge":
			print "WARNING: You're about to purge an entire folder. Type 'purge' to continue."
			really_sure = raw_input("> ")
			
			if really_sure != "purge":
				raise "User aborted purge operation"
		else:
			raise "invalid action"
		
		self.archive(action, date)
		print "Done!"
	
	#
	# Perform the archival
	#
	def archive(self, action, date):
		c = imaplib.IMAP4_SSL(self.hostname)
		c.debug = 1
		c.login(self.username, self.password)
		c.select(self.folder)
		
		t = None
		ids = []
		
		if action == "archive":
			t, [ids] = c.search(None, 'BEFORE', date)
		elif action == "purge":
			t, [ids] = c.search(None, 'ALL')
		else:
			raise "invalid action"
		
		if action == "archive":
			mbox = mailbox.mbox(self.mbox_filename)
			mbox.lock()

		for i in ids.split():
			print "getting %s" % i
			t, msg_data = c.fetch(i, '(RFC822)')
			for response_part in msg_data:
				if isinstance(response_part, tuple):
					if action == "archive":
						print "archiving %s" % i
						msg = email.message_from_string(response_part[1])
						mbox.add(msg)
						
					if self.delete_p:
						print "deleting %s" % i
						t, response = c.store(i, '+FLAGS', r'(\Deleted)')
		
		if action == "archive":
			mbox.flush()
			mbox.unlock()
		
		if self.delete_p:
			typ, response = c.expunge()
	
if __name__ == '__main__':
	a = GmailArchiver()
	a.run()
