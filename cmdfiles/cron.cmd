@echo off
:: -------------------------------------------------------------------
:: This is an attempt to start satpy scripts in a way similar to cron.
:: This must be scheduled with the Windows 10 scheduler every minute!
:: Start time for this Windows shedule must be anytime at second 01 .
:: This has been tested on a Windows 10 PRO PC that attaches to SAMBA.
:: If the scheduler runs it with highest privileges Z: is not visible.
:: Run this as user (with privileges) that has the miniconda3 install.
:: This is mostly a copy of the crontab I used with GNU/Linux PC Luna.
:: IF YOU EDIT THIS FILE MAKE SURE THE RESPECTIVE SCHEDULE IS INACTIVE
::
:: CH-3123 Belp, 2022/12/10      License GPL3       (c) Ernst Lobsiger
:: -------------------------------------------------------------------

:: The main directory
SET toodir=C:\SPStools

:: My file system layout
set LEO=%toodir%\LEOscripts
set GEO=%toodir%\GEOscripts
set CMD=%toodir%\cmdfiles

:: Now activate the Miniconda3 environment (pytroll)  
call %userprofile%\miniconda3\Scripts\activate pytroll

:: Get UTC date and time (whatever the user has as local settings) and split it
:: to integer variables in subroutine :SPLINT like "202212021205" 2022 12 2 12 5
FOR /f  %%G in ('"PowerShell (Get-Date).ToUniversalTime().ToString(\"yyyMMddHHmm\")"') do call :SPLINT %%G

:: DEBUG echo %now% %yea% %mon% %day% %hou% %min%

:: ***************************************************************
:: Only one job per satellite is allowed to run at a certain time!
:: This is especially critical for satellites that decompress raw
:: data to their tmp directories first (MSG2/3/4, HIMA8, MetopB/C).
:: These sats should never be treated in in different instances of
:: this script that run simultaneously. Keep in mind that the call
:: statements below will be executed by CMD one after the other.
:: ***************************************************************

:: Make one or more GEO frames/images every hour
:: MSG3 rss images must be computed < 5 minutes!

call :GEOmin  1  5 %GEO%\MSG3-isomrss.py  -6
call :GEOmin  1  5 %GEO%\MSG3-oaserss.py  -6
call :GEOmin  2 15 %GEO%\MSG4-msg_fes_rss.py -17
call :GEOmin 32 60 %GEO%\MSG4-westminster.py -17
call :GEOmin  3 15 %GEO%\MSG2-msg_ioc_rss.py -18
call :GEOmin 33 60 %GEO%\MSG2-afghanistan.py -18
call :GEOmin  4 10 %GEO%\HIMA8-hima_f_rss.py -44
call :GEOmin  4 10 %GEO%\GOES18-goes_wf_rss.py -44
call :GEOmin  0 10 %GEO%\GOES16-goes_ef_rss.py -50
call :GEOmin  0 10 %GEO%\GOES16-caribbean.py -50

:: Make DAY and NIG passes of LEO satellites (accounting for timeliness).
:: Again prevent MetopB/C satellites from imaging overlapping areas (that
:: may in part use the same data) with different instances of this script
:: that run simultaneosuly. E.g. if you want a MetopC isleofman DAY single
:: pass plus a westminster DAY multi then start those either at the same
:: minute or with a timely distance that makes an interference impossible.

:: Aqua:  Maximum timeliness 14143 seconds, overhead eurol DAY 12:57 + 05:00
call :LEOpic 57 17 %LEO%\Aqua-eurol.py 0 DAY
:: Aqua:  Maximum timeliness 14143 seconds, overhead eurol NIG 02:11 + 05:00
call :LEOpic 11 7 %LEO%\Aqua-eurol.py 0 NIG 

:: Aqua:  Maximum timeliness 14143 seconds, overhead isleofman DAY 13:08 + 05:00
call :LEOpic 8 18 %LEO%\Aqua-isleofman.py 0 DAY
:: Aqua:  Maximum timeliness 14143 seconds, overhead isleofman NIG 02:41 + 05:00
call :LEOpic 41 7 %LEO%\Aqua-isleofman.py 0 NIG

:: Terra: Maximum timeliness 14324 seconds, overhead eurol DAY 10:55 + 05:00
call :LEOpic 55 15 %LEO%\Terra-eurol.py 0 DAY
:: Terra: Maximum timeliness 14324 seconds, overhead eurol NIG 21:41 + 05:00
call :LEOpic 41 2 %LEO%\Terra-eurol.py -5 NIG

:: Terra: Maximum timeliness 14324 seconds, overhead isleofman DAY 11:25 + 05:00
call :LEOpic 25 16 %LEO%\Terra-isleofman.py 0 DAY
:: Terra: Maximum timeliness 14324 seconds, overhead isleofman NIG 21:53 + 05:00
call :LEOpic 53 2 %LEO%\Terra-isleofman.py -5 NIG


:: Metop Global Data Service (GDS) /https://www.eumetsat.int/metop-gds
:: Timeliness AVHRR Level 1 =  2hrs 15mins / WORST CASE ADD 3hrs 6mins

:: Measured with own script MetopB: Maximum timeliness 3661 seconds
:: Overhead isleofman DAY 10:37 + 02:00
call :LEOpic 37 12 %LEO%\MetopB-isleofman.py 0 DAY
:: Overhead isleofman NIG 20:59 + 02:00
call :LEOpic 59 22 %LEO%\MetopB-isleofman.py 0 NIG

:: Measured with own script MetopC: Maximum timeliness 6266 seconds
:: Overhead isleofman DAY 10:38 + 02:45
call :LEOpic 23 13 %LEO%\MetopC-isleofman.py 0 DAY
:: Overhead isleofman NIG 21:00 + 02:45
call :LEOpic 45 23 %LEO%\MetopC-isleofman.py 0 NIG


:: For EARS disseminated LEO satellites add 50+30=80 Minutes to optimum overhead
:: FY3D: overhead svalbard DAY 09:08 + 01:20
call :LEOpic 28 10 %LEO%\FY3D-svalbard.py 0 DAY
:: FY3D: overhead svalbard NIG 03:45 + 01:20
call :LEOpic 5 5 %LEO%\FY3D-svalbard.py 0 NIG
:: NOAA20: overhead switzerland DAY 12:14 + 01:20
call :LEOpic 33 13 %LEO%\NOAA20-switzerland.py 0 DAY
:: NOAA20: overhead switzerland NIG 01:30 + 01:20
call :LEOpic 49 2 %LEO%\NOAA20-switzerland.py 0 NIG
:: SNPP: overhead switzerland DAY 12:14 + 01:20
call :LEOpic 35 13 %LEO%\SNPP-switzerland.py 0 DAY
:: SNPP: overhead switzerland NIG 01:30 + 01:20
call :LEOpic 51 2 %LEO%\SNPP-switzerland.py 0 NIG

:: Sentinel-3A and Sentinel-3B are expected overhead Switzerland 10:04 UTC
:: Maximum timeliness measured with own script S3A=10981 S3B=10621 seconds
:: We schedule Sentinel-3X satellites 10:04 + 3.05 hours + 1 hour (slack)!
call :LEOpic  4 14 %LEO%\Sen3A-switzerland.py 0 DAY
call :LEOpic  8 14 %LEO%\Sen3B-switzerland.py 0 DAY
call :LEOpic 12 14 %LEO%\Sen3X-switzerland.py 0 DAY

:: Make four NOAA Ocean Prediction Center (OPC) overlays (Atlantic and Pacific)
call :MSLPcmd 45 3 6 %CMD%\OPC-overlays.cmd
:: Make NOAA/OPC MSLP overlays every 6 hours for MSG4, GOES16, GOES18 and HIMA8
call :GEOhou 50 3 6 %GEO%\MSG4-MSLP-opcae.py   -230
call :GEOhou 53 3 6 %GEO%\GOES16-MSLP-opcaw.py -233
call :GEOhou 54 3 6 %GEO%\GOES18-MSLP-opcpe.py -234
call :GEOhou 56 3 6 %GEO%\HIMA8-MSLP-opcpw.py  -236

:: Make UK-MetOffice (UKMO) small/large/xlarge overlays (Atlantic and Europe)
call :MSLPcmd  5 2 6 %CMD%\UKMO-overlays.cmd
call :MSLPpy  10 2 6 %CMD%\DWDSAT-overlays.py
:: Image a time slot from way back, take care not to interfere with MSG4 above
call :GEOhou  20 2 6 %GEO%\MSG4-MSLP-ukmox.py -140

:: Make Deutscher Wetterdienst (DWD) overlays (Atlantic and Europe)
call :MSLPcmd 58 0 1 %CMD%\DWD-overlays.cmd
:: Image a time slot from way back, take care not to interfere with MSG4 above
call :GEOhou 35 1 3 %GEO%\MSG4-MSLP-dwdx.py -275

:: Update TLE file 01:01 at day 1 of month
call :TLEpy 1 1 1 %CMD%\Update_TLE_file.py

:: All done!
goto :eof


:GEOmin
:: Starting a script frequently when Minute (now) % Minute_Step == Start_Minute
:: PARAMETERS: Start_Minute, Minute_Step, Script_to_run, MinuteOffset from now
:: NO leading "0" allowed! This is primarily used for movie frame generation.
set /a mm=min%%%2
if NOT %mm%==%1 goto :eof
:: We got a hit, do start the respective python script with MinuteOffset from now
for /f  %%G in ('"PowerShell Get-Date(Get-Date -Year %yea% -Month %mon% -Day %day% -Hour %hou% -Minute %min%).AddMinutes(%4) -uformat +%%Y%%m%%d%%H%%M"') do set slot=%%G
echo %3 %slot%
python %3 %slot%
goto :eof

:GEOhou
:: PARAMETERS: Start_Minute, Start_Hour, Hour_Step, Script_to_run, MinuteOffset from now
:: NO leading "0" allowed! This was added for hourly GEOpics stepped with "Hour_step"
if NOT %1==%min% goto :eof 
set /a hh=hou%%%3
if NOT %hh%==%2 goto :eof 
:: We got a hit, do start the respective python script with MinuteOffset from now
for /f  %%G in ('"PowerShell Get-Date(Get-Date -Year %yea% -Month %mon% -Day %day% -Hour %hou% -Minute %min%).AddMinutes(%5) -uformat +%%Y%%m%%d%%H%%M"') do set slot=%%G
echo %4 %slot%
python %4 %slot%
goto :eof

:LEOpic
:: Starting a LEO pass with maybe HourOffset <= 0 to get yesterday instead of today
:: PARAMETERS: Start_Minute, Start_Hour, Script_to_run, HourOffset (for yesterday) 
if NOT %1==%min% goto :eof 
if NOT %2==%hou% goto :eof 
:: We got a hit, do start the respective python script with HourOffset from now
for /f  %%G in ('"PowerShell Get-Date(Get-Date -Year %yea% -Month %mon% -Day %day% -Hour %hou% -Minute %min%).AddHours(%4) -uformat +%%Y%%m%%d%5"') do set pass=%%G
echo %3 %pass%
python %3 %pass%
goto :eof

:MSLPcmd
:: PARAMETERS: Start_Minute, Start_Hour, Hour_Step, Script_to_run.cmd
:: This is used to prepare all sorts of MSLP overlays (starts *.cmd)
if NOT %1==%min% goto :eof 
set /a hh=hou%%%3
if NOT %hh%==%2 goto :eof 
echo %4
call %4
goto :eof

:MSLPpy
:: PARAMETERS: Start_Minute Start_Hour Hour_Step Script_to_run.py
:: As above to prepare UKMOX MSLP overlays (starts *.py)
if NOT %1==%min% goto :eof 
set /a hh=hou%%%3
if NOT %hh%==%2 goto :eof 
echo %4
python %4
goto :eof

:TLEpy
:: PARAMETERS: Start_Minute, Start_Hour, Start_Day, Script_to_run.py
:: Runs once in the current month (only used to update the TLE file)
if NOT %3==%day% goto :eof 
if NOT %2==%hou% goto :eof 
if NOT %1==%min% goto :eof 
echo %4
python %4
goto :eof

:SPLINT
:: Split to int yea mon day hou min
set now=%1
set yea=%now:~0,4%
set mon=%now:~4,2%
if %mon:~0,1%==0 set mon=%mon:~1,1%
set day=%now:~6,2%
if %day:~0,1%==0 set day=%day:~1,1%
set hou=%now:~8,2%
if %hou:~0,1%==0 set hou=%hou:~1,1%
set min=%now:~10,2%
if %min:~0,1%==0 set min=%min:~1,1%
goto :eof


