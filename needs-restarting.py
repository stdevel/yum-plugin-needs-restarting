#!/bin/env python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# Copyright 2009 Red Hat Inc
# written by Seth Vidal

# look through list of running apps
# report any app which was updated after it was started
# (and therefore needs to be restarted)


# for each /proc/number-dir
# get stat of create time on that dir
# open up smaps and search for all lines with 'fd:' in them
# take filename
# search for the package owning that file
# make a list of installtimes of all pkgs of the files the program has open
# sort the list
# if the dir create time is < the largest time on the installtimes list
# then output the pid and process cmdline as needing to be restarted

#TODO:
# maybe note deleted files which are not owned by any pkg but which an app
# is still using
# output userids, too?



from yum.plugins import PluginYumExit, TYPE_INTERACTIVE
from os import popen
import sys
import os
import yum
import yum.misc
import glob
import stat
sys.path.insert(0,'/usr/share/yum-cli')
import utils
from yum import config


requires_api_version = '2.1'
plugin_type = (TYPE_INTERACTIVE,)
#set of pids needing restart
needing_restart = set()


def return_running_pids(uid=None):
	mypid = os.getpid()
	pids = []
	for fn in glob.glob('/proc/[0123456789]*'):
		if mypid == os.path.basename(fn):
			continue
		if uid: # meaning we're not root and we've added -u
			if os.stat(fn)[stat.ST_UID] != uid:
				continue
		pids.append(os.path.basename(fn))
	return pids

def get_open_files(pid):
	files = []
	smaps = '/proc/%s/smaps' % pid
	try:
		with open(smaps, 'r') as maps_f:
			maps = maps_f.readlines()
	except (IOError, OSError), e:
		#print >>sys.stderr, "Could not open %s" % smaps
		print "Could not open %s" % smaps
		return files
	
	for line in maps:
		slash = line.find('/')
		if slash == -1 or line.find('00:') != -1: # if we don't have a '/' or if we fine 00: in the file then it's not _REALLY_ a file
			continue
		line = line.replace('\n', '')
		filename = line[slash:]
		filename = filename.split(';')[0]
		filename = filename.strip()
		if filename not in files:
			files.append(filename)
	return files

def get_service_by_binary(cmd):
	yb = yum.YumBase()
	yb.doConfigSetup(debuglevel=0, errorlevel=0)
	try:   
		pkgs = yb.rpmdb.searchFiles(cmd)
		#print pkgs
		files = pkgs[0].returnFileEntries()
		matches = [s for s in files if "init.d" in s]
		if len(matches) > 0:
			k = matches[0].rfind("/")
			return matches[0][k+1:]
		else: return False
	except:
		return False

def main(args):
    #(opts, args)  = parseargs(args)
    global needing_restart
    global exclude

    my = yum.YumBase()
    my.preconf.init_plugins=False
    if hasattr(my, 'setCacheDir'):
        my.setCacheDir()
    my.conf.cache = True
    
    myuid = None
    #if opts.useronly:
    #    myuid = os.getuid()
    
    #needing_restart = set()

    boot_time = utils.get_boot_time()
    for pid in return_running_pids(uid=myuid):
        try:
            pid_start = utils.get_process_time(int(pid), boot_time)['start_time']
        except (OSError, IOError), e:
            continue
        found_match = False
        for fn in get_open_files(pid):
            if found_match:
                break
   
            just_fn = fn.replace('(deleted)', '')
            just_fn = just_fn.strip()
            bogon = False
            # if the file is in a pkg which has been updated since we started the pid - then it needs t
            for pkg in my.rpmdb.searchFiles(just_fn):
                if float(pkg.installtime) > float(pid_start):
                    needing_restart.add(pid)
                    found_match = True
                    continue
                if just_fn in pkg.ghostlist:
                    bogon = True
                    break
   
            if bogon:
                continue

            # if the file is deleted
            if fn.find('(deleted)') != -1:
                # and it is from /*bin/* then it needs to be restarted
                if yum.misc.re_primary_filename(just_fn):
                    needing_restart.add(pid)
                    found_match = True
                    continue

                # if the file is from an old ver of an installed pkg - then assume it was just updated
                # new pkg doesn't have the same file names. Fabulous huh?!
                my.conf.cache = False
                for oldpkg in my.pkgSack.searchFiles(just_fn): # ghostfiles are always bogons
                    if just_fn in oldpkg.ghostlist:
                        continue
                    if my.rpmdb.installed(oldpkg.name):
                        needing_restart.add(pid)
                        found_match = True
                        break

    #removing blacklisted procs
    removeMe = set()
    for pid in needing_restart:
        try:
            cmdline = open('/proc/' + pid + '/cmdline', 'r').read()
        except (OSError, IOError), e:
            print "Couldn't access process information for %s: %s" % (pid, str(e))
            continue
        matches=[s for s in exclude if s in cmdline]
        if len(matches) != 0 and len(matches[0]) > 0:
		#print "I'd like to remove PID #"+pid
		removeMe.add(pid)
    needing_restart = set(needing_restart) - set(removeMe)
    
    if len(needing_restart) > 0:
	print "You might want to restart the following processes:"
        for pid in needing_restart:
            try:
                cmdline = open('/proc/' +pid+ '/cmdline', 'r').read()
            except (OSError, IOError), e:
                print "Couldn't access process information for %s: %s" % (pid, str(e))
                continue
            print '? (PID %s, %s)' % (pid, cmdline)
    else:
        print "No processes using old files, nice job."

class NeedsRestartingCommand:
	
	def getNames(self):
		return ['needs-restarting']
	
	def getUsage(self):
		return ""
	
	def getSummary(self):
		return "List processes that are using old files"
	
	def doCheck(self, base, basecmd, extcmds):
		pass
	
	def doCommand(self, base, basecmd, extcmds):
		main(None)
		rc = 0
		return rc, ['' ""]
	
	def needTs(self, base, basecmd, extcmds):
		return False



def config_hook(conduit):
	'''
	Yum Plugin Config Hook: 
	Add the 'needs-restarting' command.
	'''
	conduit.registerCommand(NeedsRestartingCommand())
	
def init_hook(conduit):
	global exclude
	conduit_conf = conduit.getConf()
	exclude = str(conduit.confString('main', 'excludeProcs', conduit_conf.exclude)).split(",")

	excludeLength = len(exclude)
	
	if excludeLength > 0:
		print "You blacklisted (%s Elements):" % (excludeLength-1)
		for hit in exclude:
			print hit
	print ""
