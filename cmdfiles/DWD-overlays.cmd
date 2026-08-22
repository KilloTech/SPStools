@echo off
:: ----------------------------------------------------------------------------------------------
:: This CMD script makes overlays to be used with the PyTROLL/Satpy for EUMETCast V 4.1
:: Input files are *.png from OpenData.dwd.de, output files are fourteen kinds of png32
::
:: Primary input file name:
:: content.log.bz2           This file should not be seen, deleted after overlays are processed 
:: Typical output file names:
:: area-bc-202111261200.png   Pressure, grid lines black, fronts colourized  set fill_value=255
:: area-wc-202111261200.png   Pressure, grid lines white, fronts coluorized  set fill_value=0
:: area-bb-202111261200.png   Pressure, grid lines, coast, fronts are black  set fill_value=255
:: area-ww-202111261200.png   Pressure, grid lines, coast, fronts are white  set fill_value=0
::
:: Windows finally comes with curl.exe and tar.exe. We use curl for download. If this doesn't
:: work for you then get a CLI wget.exe as fallback. I have used GNU Wget 1.15 built on mingw32
:: You can download this version from https://eternallybored.org/misc/wget   ... or ask David
::
:: We use flock and exit handlers under GNU/Linux Bash. There is no such thing under Windows CMD.
:: That said it's up to *you* to not start more than one instance of this script at the same time.
::
:: ** WE USE NO QUOTES "", NO TRAILING BLANKS, NO BAD WINDOWS HABITS OF PATH NAMES WITH SPACES **
::
:: CH-3123 Belp, 2022/12/10                  License GPL3                          Ernst Lobsiger
:: ----------------------------------------------------------------------------------------------

:: The main directories
set toodir=C:\SPStools
set datdir=D:\SPSdata

:: Where we wget our stuff from DWD
set BASE_URL=https://opendata.dwd.de/weather/charts
:: That's the bz2 zipped content file we use, issue is LATEST
set content_bz2=content.log.bz2
:: That's the unzipped content file we use, issue is LATEST
set content=%content_bz2:~0,-4%
:: We only curl or wget files not already processed earlier
set CURL_LIST=curl.list
set WGET_LIST=wget.list
:: Temporary working directory (must exist)
set tmp=%datdir%\tmpdirs\xmslp

:: Default path to ImageMagick convert.exe
set convert=%toodir%\exefiles\convert.exe
:: Where to find your CLI Windows wget.exe
set cliwget=%toodir%\exefiles\wget.exe
:: Where to find a Windows program like bunzip2
set bunzip2=%toodir%\exefiles\7za
:: Output base directory for overlays (must exist)
:: Sub directories dwda, dwdn, dwdc, dwdi (must exist)
set OVR_DIR=%datdir%\overlays
:: If debugging set DEBUG=con else DEBUG=nul
set DEBUG=con

:: ******** DO NOT TOUCH THE CODE BELOW UNLESS YOU KNOW WHAT YOU DO ********

:: Main DWD colours
set red=#ff0000
set blue=#0000ff
set black=#000000
set white=#ffffff
set violet=#ee82ee
set gray20=#333333

del %tmp%\%CURL_LIST% /f 2>%DEBUG%
del %tmp%\%WGET_LIST% /f 2>%DEBUG%
del %tmp%\content.log* /f 2>%DEBUG%
del %tmp%\Z__C_EDZW_*.png* /f 2>%DEBUG%

:: Download the LATEST mslp charts. Ask approximately 13:45 UTC to get the 12:00 UTC issue

curl --remote-time -o %tmp%\%content_bz2% %BASE_URL%/%content_bz2%
:: If curl does not work for you comment/uncomment the line above/below
:: %cliwget% --no-check-certificate -P %tmp% %BASE_URL%/%content_bz2%
if not exist %tmp%\%content_bz2% (
    echo Sorry, could not download %content_bz2%!
    goto :eof
) else (
    :: bunzip2 the LATEST content
    %bunzip2% x -so %tmp%\%content_bz2% > %tmp%\%content%
) 

:: Making todo list for colour overlays
for /f "tokens=1 delims=|" %%f in ('findstr /R analysis.*an_dwd.*WV12.png %tmp%\content.log') do call :TODO_COLOUR "%%f"
:: Making todo list for monochrome overlays
for /f "tokens=1 delims=|" %%f in ('findstr /R analysis.*an_dwd.*WV12SW.png %tmp%\content.log') do call :TODO_MONO "%%f"
:: Making todo list for ICON13 monochrome overlays
for /f "tokens=1 delims=|" %%f in ('findstr /R analysis.*p00_na.*WV11.png %tmp%\content.log') do call :TODO_ICON "%%f"

:: Downloading all files of the todo list
(for /f %%f in (%tmp%\%CURL_LIST%) do curl --remote-time -o %tmp%\%%f %BASE_URL%/analysis/%%f) 2>%DEBUG%
:: If curl does not work for you comment/uncomment the line above/below
:: (%cliwget% --no-check-certificate -q -nd -np -P %tmp% -i %tmp%\%WGET_LIST%) 2>%DEBUG%

:: Processing colourized overlays
(for /f "tokens=1" %%f in ('dir /B %tmp%\Z__C_EDZW*WV12.png') do call :DO_COLOUR "%%f") 2>%DEBUG%

:: Processing monochrome overlays
(for /f "tokens=1" %%f in ('dir /B %tmp%\Z__C_EDZW*WV12SW.png') do call :DO_MONO "%%f") 2>%DEBUG%

:: Processing ICON13 monochrome overlays
(for /f "tokens=1" %%f in ('dir /B %tmp%\Z__C_EDZW*WV11.png') do call :DO_ICON "%%f") 2>%DEBUG%

:: All done!
goto :eof

:: --------------------------- Subroutines follow below --------------------------------

:TODO_COLOUR
  :: Strip ""
  set f=%~1
  set area=%f:~53,4%
  if %area%==dwdn (set datim=%f:~75,12%) else (set datim=%f:~74,12%)
  :: Is one of the bc OR wc overlays missing ?
  if not exist "%OVR_DIR%\%area%\%area%-bc-%datim%.png" (
     echo %f:~11% >> %tmp%\%CURL_LIST%
     echo %BASE_URL%/%f:~2% >> %tmp%\%WGET_LIST%
  ) else (
     if not exist "%OVR_DIR%\%area%\%area%-wc-%datim%.png" (
       echo %f:~11% >> %tmp%\CURL_LIST%
       echo %BASE_URL%/%f:~2% >> %tmp%\%WGET_LIST%
     )
  )
goto :eof


:TODO_MONO
  :: Strip ""
  set f=%~1
  set area=%f:~53,4%
  if %area%==dwdn (set datim=%f:~75,12%) else (set datim=%f:~74,12%)
  :: Is one of the bb OR ww overlays missing ?
  if not exist "%OVR_DIR%\%area%\%area%-bb-%datim%.png" (
     echo %f:~11% >> %tmp%\%CURL_LIST%
     echo %BASE_URL%/%f:~2% >> %tmp%\%WGET_LIST%
  ) else (
     if not exist "%OVR_DIR%\%area%\%area%-ww-%datim%.png" (
       echo %f:~11% >> %tmp%\%CURL_LIST%
       echo %BASE_URL%/%f:~2% >> %tmp%\%WGET_LIST%
     )
  )
goto :eof


:TODO_ICON
  :: Strip ""
  set f=%~1
  set area=dwdi
  set datim=%f:~69,12%
  :: Is one of the bb OR ww overlays missing ?
  if not exist "%OVR_DIR%\%area%\%area%-bb-%datim%.png" (
     echo %f:~11% >> %tmp%\%CURL_LIST%
     echo %BASE_URL%/%f:~2% >> %tmp%\%WGET_LIST%
  ) else (
     if not exist "%OVR_DIR%\%area%\%area%-ww-%datim%.png" (
       echo %f:~11% >> %tmp%\%CURL_LIST%
       echo %BASE_URL%/%f:~2% >> %tmp%\%WGET_LIST%
     )
  )
goto :eof


:DO_COLOUR
  :: Strip ""
  set f=%~1
  set area=%f:~42,4%
  :: Replaces a CASE statement
  goto :%area%
  :dwda
    echo Processing Western Europe, %area% colourized
    set datim=%f:~63,12%
  goto :ESAC
  :dwdn
    echo Processing North Atlantic, %area% colourized
    set datim=%f:~64,12%
  goto :ESAC
  :dwdc
    echo Processing Stereographic,  %area% colourized
    set datim=%f:~63,12%
  :ESAC
  set f=%tmp%\%f%

  ::OK %convert% %f%  +transparent %black% ^( %f% +transparent %red% ^) -composite ^( %f% +transparent %blue% ^) -composite ^( %f% +transparent %violet% ^) -composite		 PNG32:%OVR_DIR%\%area%\%area%-bc-%datim%.png

  ::OK %convert% %f% +transparent %black%  ^( %f% +transparent %red% ^) -composite ^( %f% +transparent %blue% ^) -composite ^( %f% +transparent %violet% ^) -composite   -fill %white% -opaque %black% PNG32:%OVR_DIR%\%area%\%area%-wc-%datim%.png

  %convert% %f%  +transparent %black% ^( %f% +transparent %red% ^) -composite ^( %f% +transparent %blue% ^) -composite ^( %f% +transparent %violet% ^) -composite PNG32:%OVR_DIR%\%area%\%area%-bc-%datim%.png

  %convert% %f% +transparent %black%  ^( %f% +transparent %red% ^) -composite ^( %f% +transparent %blue% ^) -composite ^( %f% +transparent %violet% ^) -composite   -fill %white% -opaque %black% PNG32:%OVR_DIR%\%area%\%area%-wc-%datim%.png

goto :eof


:DO_MONO
  :: Strip ""
  set f=%~1
  set area=%f:~42,4%
  :: Replaces a CASE statement
  goto :%area%
  :dwda
    echo Processing Western Europe, %area% monochrome
    set datim=%f:~63,12%
  goto :ESAC
  :dwdn
    echo Processing North Atlantic, %area% monochrome
    set datim=%f:~64,12%
  goto :ESAC
  :dwdc
    echo Processing Stereographic,  %area% monochrome
    set datim=%f:~63,12%
  :ESAC
  set f=%tmp%\%f%
 
  :: It seems this version of convert does not work like the one under GNU/Linux. I must try to circumwent +transparent black or white?
::OK  %convert% %f% -threshold 80%% -negate -transparent %black% -fill %black% -opaque %white% PNG32:%OVR_DIR%\%area%\%area%-bb-%datim%.png
::OK  %convert% %f% -threshold 80%% -negate -transparent %black% PNG32:%OVR_DIR%\%area%\%area%-ww-%datim%.png

%convert% %f% -threshold 80%% -negate -transparent %black% -fill %black% -opaque %white% PNG32:%OVR_DIR%\%area%\%area%-bb-%datim%.png

%convert% %f% -threshold 80%% -negate -transparent %black% PNG32:%OVR_DIR%\%area%\%area%-ww-%datim%.png

goto :eof


:DO_ICON
  :: Strip ""
  set f=%~1
  set area=dwdi
  set datim=%f:~58,12%
  echo Processing Central Europe, %area% monochrome
  set f=%tmp%\%f%
  %convert% %f% -threshold 80%% ^( %f% -fill %black% -opaque %gray20% +transparent %black% ^) -composite -transparent %white% PNG32:%OVR_DIR%\%area%\%area%-bb-%datim%.png

  %convert% %f% -threshold 80%% ^( %f% -fill %black% -opaque %gray20% +transparent %black% ^) -composite -negate -transparent %black% PNG32:%OVR_DIR%\%area%\%area%-ww-%datim%.png

goto :eof
