@echo off
::---------------------------------------------------------------
:: Script to download (fullsize) UKMO Ground Pressure Charts from
:: https://www.weathercharts.org and make PNG32 bb + ww overlays.
:: Results are 2148 pixels wide and 1452 pixels high (area ukmol)
:: Added smaller version for completeness 1040 x 727 (area ukmos)
::
:: Pressure lines and text annotation black, needs fill_value=255
:: ukmo-bb-YYYYmmddHHMM.png, Stereographic Projection,   6 hourly
:: Pressure lines and text annotation white, needs fill_value = 0
:: ukmo-ww-YYYYmmddHHMM.png, Stereographic Projection,   6 hourly
::
:: This script has to be scheduled 02:05 and every 6 hours later.
:: 05 2,8,14,20 * * * user script (05 2-20/6 * * *  also works !)
::
:: CH-3123 Belp, 2022/12/10    License GPL3    (c) Ernst Lobsiger
::---------------------------------------------------------------

:: Until further notice from UKMO we use this area for overlays:
:: (this has been optimized under GNU/Linux, with minor changes)

::
:: ukmos:
::   description: UK MetOffice (Small size Ground Pressure Overlay from www.weathercharts.net)
::   projection:
::     proj: stere
::     ellps: WGS84
::     lat_0:  90.0
::     lon_0: -35.0
::   shape:
::     height: 727
::     width: 1074
::   area_extent:
::     lower_left_xy:  [-2173000.0, -6325000.0]
::     upper_right_xy: [ 6328000.0,  -587500.0]
::
:: ukmol:
::   description: UK MetOffice (Large size Ground Pressure Overlay from www.weathercharts.net)
::   projection:
::     proj: stere
::     ellps: WGS84
::     lat_0: 90.0
::     lon_0: -35.0
::   shape:
::     height: 1452
::     width:  2148
::   area_extent:
::     lower_left_xy: [-2180000.0, -6319000.0]
::     upper_right_xy: [6328000.0, -588000.0]
::

:: Windows finally comes with curl.exe and tar.exe. We use curl for download. If this doesn't
:: work for you then get a CLI wget.exe as fallback. I have used GNU Wget 1.15 built on mingw32
:: You can download this version from https://eternallybored.org/misc/wget   ... or ask David
::
:: We use flock and exit handlers under GNU/Linux Bash. There is no such thing under Windows CMD.
:: That said it's up to *you* to not start more than one instance of this script at the same time.

::
::
:: ******** YOU USE THIS AT YOUR OWN RISK AND PERIL ********      2022/09/20      Ernst Lobsiger
::
::

:: The main directories
set toodir=C:\SPStools
set datdir=D:\SPSdata

:: You must have write access to TMP_DIR
set TMP_DIR=%datdir%\tmpdirs\xmslp

:: Output directory for small\large overlays
set OVR_DIR=%datdir%\overlays

:: ****************************************************
:: Touch this stuff below only if you know what you do!
:: ****************************************************

:: The only place I found that has the ukmo fullsize version
set BASE_URL=https://www.weathercharts.net/ukmo_mslp_analysis
set UKMOS=ppva.gif
set UKMOL=ppva_fullsize.gif

:: Where to find your CLI Windows wget.exe
set CLIWGET=%toodir%\exefiles\wget.exe
:: Default path to ImageMagick convert.exe
set CONVERT=%toodir%\exefiles\convert.exe


del %TMP_DIR%\%UKMOS%* /f

:: Download the LATEST small size UKMO mslp chart.
curl --remote-time -o %TMP_DIR%\%UKMOS% %BASE_URL%/%UKMOS%
:: If curl does not work for you comment/uncomment the line above/below
:: %CLIWGET% -P %TMP_DIR% --no-check-certificate %BASE_URL%/%UKMOS%

if not exist %TMP_DIR%\%UKMOS% (
  echo Sorry, could not download %UKMOS% !
  goto :eof
) 

:: Yes, this *must* stay on one line. It's the longest CMD statement I have ever written. And it works ;-) ...
for /f %%G in ('"PowerShell (Get-Date '1/1/1970').AddSeconds([long][math]::floor((Get-Date -Date (Get-ChildItem %TMP_DIR%\%UKMOS%).lastwritetime -uformat +%%s)/21600)*21600).ToString(\"yyyMMddHH\")"') do set issue=%%G00

%CONVERT% %TMP_DIR%\%UKMOS% -crop 1070x723+2+33 -bordercolor black -border 2x2 -threshold 80%% +antialias -transparent white PNG32:%OVR_DIR%\ukmos\ukmos-bb-%issue%.png
%CONVERT% %TMP_DIR%\%UKMOS% -crop 1070x723+2+33 -bordercolor black -border 2x2 -threshold 80%% +antialias -negate -transparent black PNG32:%OVR_DIR%\ukmos\ukmos-ww-%issue%.png


del %TMP_DIR%\%UKMOL%* /f

:: Download the LATEST large size UKMO mslp chart.
curl --remote-time -o %TMP_DIR%\%UKMOL% %BASE_URL%/%UKMOL%
:: If curl does not work for you comment/uncomment the line above/below
:: %CLIWGET% -P %TMP_DIR% --no-check-certificate %BASE_URL%/%UKMOL%

if not exist %TMP_DIR%\%UKMOL% (
  echo Sorry, could not download %UKMOL% !
  goto :eof
) 

:: Yes, this *must* stay on one line. It's the longest CMD statement I have ever written. And it works ;-) ...
for /f %%G in ('"PowerShell (Get-Date '1/1/1970').AddSeconds([long][math]::floor((Get-Date -Date (Get-ChildItem %TMP_DIR%\%UKMOL%).lastwritetime -uformat +%%s)/21600)*21600).ToString(\"yyyMMddHH\")"') do set issue=%%G00

%CONVERT% %TMP_DIR%\%UKMOL% -crop 2142x1446+3+66 -bordercolor black -border 3x3 -threshold 80%% +antialias -transparent white PNG32:%OVR_DIR%\ukmol\ukmol-bb-%issue%.png
%CONVERT% %TMP_DIR%\%UKMOL% -crop 2142x1446+3+66 -bordercolor black -border 3x3 -threshold 80%% +antialias -negate -transparent black PNG32:%OVR_DIR%\ukmol\ukmol-ww-%issue%.png

:: All done!

