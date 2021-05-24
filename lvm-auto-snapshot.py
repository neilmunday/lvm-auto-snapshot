#!/usr/bin/env python3

#
# A script that can be used to automatically create LVM snapshots for back-up purposes.
#
# Copyright (C) 2021 Neil Munday
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import argparse
import datetime
import os
import logging
import json
import re
import shlex
import subprocess
import sys

def die(msg):
    '''
    Exit the program with an error message.
    '''
    logging.error(msg)
    sys.exit(1)

def runCommand(cmd):
	'''
	Execute the given command and return a tuple that contains the
	return code, std out and std err output.
	'''
	logging.debug('running %s' % cmd)
	process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()

	if process.returncode != 0:
		die("command %s failed: %s\nstdout: %s\nstderr:" % (cmd, stdout, stderr))

	logging.debug("stdout: %s\nstderr: %s" % (stdout, stderr))

	return (process.returncode, stdout, stderr)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Creates a LVM snapshot of the given LV for a given number of days', add_help=True)
    parser.add_argument('-v', '--verbose', help='Turn on debug messages', dest='verbose', action='store_true')
    parser.add_argument('-d', '--days', dest='days', help='Days to keep the snapshot for', required=True, type=int)
    parser.add_argument('-l', '--lv', dest='lv', help='Logical volume', required=True)
    parser.add_argument('-g', '--vg', dest='vg', help='Volume group', required=True)
    parser.add_argument('-s', '--size', dest='size', help='Size of the snapshot in GB', required=True, type=int)
    args = parser.parse_args()

    logLevel = logging.INFO
    if args.verbose:
        logLevel = logging.DEBUG

    logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logLevel)

    datestr = datetime.datetime.now().strftime("%Y.%m.%d")
    logging.debug(datestr)

    rtn, stdout, stderr = runCommand("lvs -o vg_name,lv_name --report-format=json")
    data = json.loads(stdout)

    if "report" not in data:
        die("Invalid JSON from lvs command:\n%s" % data)

    lvRe = re.compile("%s_backup_([0-9]+)\.([0-9]+)\.([0-9]+)" % args.lv)

    lvFound = False
    backupLvName = "%s_backup_%s" % (args.lv, datestr)
    backupLvFound = False
    for lv in data["report"][0]["lv"]:
        logging.debug(lv)
        if lv["vg_name"] == args.vg:
            if lv["lv_name"] == args.lv:
                found = True
            elif lv["lv_name"] == backupLvName:
                backupLvFound = True
            else:
                match = lvRe.match(lv["lv_name"])
                if match:
                    logging.debug("found re match for %s/%s" % (lv["vg_name"], lv["lv_name"]))
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    theDate = datetime.date(year, month, day)
                    daysDiff = (datetime.date.today() - datetime.date(year, month, day)).days
                    if daysDiff > args.days:
                        logging.info("Removing snapshot %s/%s" % (lv["vg_name"], lv["lv_name"]))
                        runCommand("lvremove -f %s/%s" % (lv["vg_name"], lv["lv_name"]))
                    else:
                        logging.info("Keeping snapshot %s/%s" % (lv["vg_name"], lv["lv_name"]))

    if found:
        logging.debug("Found LV")
    else:
        die("Could not find LV %s/%s" % (args.vg, args.lv))

    if backupLvFound:
        logging.info("Back-up LV already exists for today")
        sys.exit(0)

    # create snapshot
    logging.info("creating snapshot for %s/%s" % (args.vg, args.lv))
    runCommand("lvcreate --size %sG --permission r --snapshot '%s/%s' --name '%s'" % (args.size, args.vg, args.lv, backupLvName))

    sys.exit(0)
