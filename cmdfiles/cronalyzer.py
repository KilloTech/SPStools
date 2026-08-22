#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Gives an overview of what's happening if you schedule cron.cmd every minute with the Windows scheduler

# This will only work if cron.cmd is formatted as distributed. But you can :: comment to exclude calls!
# To sqeeze multiple blanks in Windows 10 cron.cmd lines (before we can split those) I use re. See URL:
# https://stackoverflow.com/questions/1546226/is-there-a-simple-way-to-remove-multiple-spaces-in-a-string
# Keep in mind that webm.cmd (CPU intensive) and tidy.cmd (HDD intensive) is scheduled outside cron.cmd.

# Belp,  2022/12/06                             License GPL3                             Ernst Lobsiger

import re

# Script to be analyzed
textfile = 'cron.cmd'
print('SPS 4.1 Windows', textfile,'(a GNU/Linux crontab replacement) analyzed with croanlyzer.py\n')
print('Keep in mind that the jobs started at minute nnnn can take several minutes to complete')
print('That said you will quite often note that more than one instance of', textfile,'is at work\n')
try:
    f = open(textfile, mode='r', encoding='ascii')
except FileNotFoundError:
    raise FileNotFoundError('Could not find file %s' % textfile)
try:
    s = f.readline()
except IOError:
    raise IOError('Could not read file %s' % textfile)

# Make a list of 1440 lists
day=[]
for i in range(0, 1440):
    day.append([])

def GEOmin(i, j, s):
    while (i < 1440):
        day[i].append(s[6:])
        i += j

def GEOhou(i, j, k, s):
    m = i + j*60
    while (m < 1440):
        day[m].append(s[6:])
        j += k
        m = i + j*60

def LEOpic(i, j, s):
    day[i+60*j].append(s[6:])

def MSLPcmd(i, j, k, s):
    m = i + j*60
    while (m < 1440):
        day[m].append(s[6:])
        j += k
        m = i + j*60

def MSLPpy(i, j, k, s):
    m = i + j*60
    while (m < 1440):
        day[m].append(s[6:])
        j += k
        m = i + j*60

def daytime(m):
    h = 0
    while (m >= 60):
        m -= 60
        h += 1
    return h, m

# Iterate through lines
while s != '':
    # Get rid of Windows 10 CR
    s = s[:-1]
    # call :GEOmin  6 10 %GEO%\GOES16-caribbean.py -96
    if s[0:12] == 'call :GEOmin':
        s = re.sub(' +',' ', s )
        t = s.split(' ')
        # print(t[2], t[3], t[4])
        GEOmin(int(t[2]), int(t[3]), t[4])
    # call :LEOpic 57 17 %LEO%\Aqua-eurol.py 0 DAY
    if s[0:12] == 'call :LEOpic':
        s = re.sub(' +',' ', s )
        t = s.split(' ')
        # print(t[2], t[3], t[4])
        LEOpic(int(t[2]), int(t[3]), t[4])
    # call :GEOhou 50 3 6 %GEO%\MSG4-MSLP-opcae.py   -230
    if s[0:12] == 'call :GEOhou':
        s = re.sub(' +',' ', s )
        t = s.split(' ')
        # print(t[2], t[3], t[4], t[5])
        GEOhou(int(t[2]), int(t[3]), int(t[4]), t[5])
    # call :MSLPcmd 45 3 6 %CMD%\OPC-overlays.cmd
    if s[0:13] == 'call :MSLPcmd':
        s = re.sub(' +',' ', s )
        t = s.split(' ')
        # print(t[2], t[3], t[4], t[5])
        MSLPcmd(int(t[2]), int(t[3]), int(t[4]), t[5])
    # call :MSLPpy  10 2 6 %CMD%\DWDSAT-overlays.py
    if s[0:12] == 'call :MSLPpy':
        s = re.sub(' +',' ', s )
        t = s.split(' ')
        # print(t[2], t[3], t[4], t[5])
        MSLPpy(int(t[2]), int(t[3]), int(t[4]), t[5])

    # Read next line
    s = f.readline()
f.close()

# Print results
for i in range(0, 1440):
  h, m = daytime(i)
  print(f'{i:04d} {h:02d}:{m:02d}', day[i])
