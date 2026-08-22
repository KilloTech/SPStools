@echo off
:: ------------------------------------------------------------------------------------------
:: This script makes webm movies. To be able to make symbolic links to frames this has to be
:: run with administrator rights??!! There is a field you can check when using the scheduler.
:: If you run this from CLI of a good old "DOS" window be sure to start CMD as administrator.
:: If you run this by right clicking its icone make sure to run it with administrator rights.
:: If you make a link (icone) to start this, be sure to check the field run as administrator.
:: Try to avoid scheduling this at the same time with heavy load production of DWD overlays.
:: *DO NEVER RUN TWO INSTANCES OF THIS SCRIPT AS THERE IS ONLY ONE TEMP DIRECTORY FOR LINKS!*
:: *IF YOU EDIT THIS STUFF BE SURE THE RESPECTIVE ENTRY IN THE WIN SCHEDULER IS DEACTIVATED!*
::
:: CH-3123 Belp, 2022/12/10                 License GPL3                   (c) Ernst Lobsiger
:: ------------------------------------------------------------------------------------------

:: The main directories
SET toodir=C:\SPStools
SET datdir=D:\SPSdata

:: That's where your products are
SET prodir=%datdir%\products
:: Scratch dir, might be set %temp%
SET tmpdir=%datdir%\tmpdirs\ffmpeg
:: We distribute an all linked in version
SET ffmpeg=%toodir%\exefiles\ffmpeg.exe

:: Identify maybe convert -identify
SET convert=%toodir%\exefiles\convert.exe
SET identify=%toodir%\exefiles\identify.exe
SET font=%datdir%\fonts\courbi.ttf

:: At hour 02 (UTC) early in the morning make full 00:00-23:55 movies of yesterday else 00:00 - NOW 
FOR /f  %%G in ('"PowerShell Get-Date (Get-Date).ToUniversalTime() -uformat +%%H"') do set hour=%%G

SET /A goback=0
if %hour%==02 SET /a goback=-10
FOR /f  %%G in ('"PowerShell Get-Date (Get-Date).ToUniversalTime().AddHours(%goback%) -uformat +%%Y%%m%%d"') do set today=%%G

:: These movies are currently produced on GNU/Linux receiver Luna. Feel free to add your own stuff..
:: They have been tested to work under Windows 10 PRO on a 10 years old PC with I7 proc and 16GB RAM

call :MAKEWEBM MSG2 airmass-msg_ioc_rss %today% 0
call :MAKEWEBM MSG2 colorized_ir_clouds-msg_ioc_rss %today% 0
call :MAKEWEBM MSG2 overview-msg_ioc_rss %today% 0

call :MAKEWEBM MSG3 overview-isomrss %today% 0
call :MAKEWEBM MSG3 ir_overview-isomrss %today% 0
call :MAKEWEBM MSG3 natural_with_night_fog-isomrss %today% 0

call :MAKEWEBM MSG3 overview-oaserss %today% 0
call :MAKEWEBM MSG3 ir_overview-oaserss %today% 0
call :MAKEWEBM MSG3 natural_with_night_fog-oaserss %today% 0

call :MAKEWEBM MSG4 airmass-msg_fes_rss %today% 0
call :MAKEWEBM MSG4 colorized_ir_clouds-msg_fes_rss %today% 0
call :MAKEWEBM MSG4 overview-msg_fes_rss %today% 0

call :MAKEWEBM GOES16 airmass-goes_ef_rss %today% 0
call :MAKEWEBM GOES16 colorized_ir_clouds-goes_ef_rss %today% 0
call :MAKEWEBM GOES16 overview-goes_ef_rss %today% 0
call :MAKEWEBM GOES16 true_color_with_night_ir_hires-caribbean %today% 1

call :MAKEWEBM GOES18 airmass-goes_wf_rss %today% 0
call :MAKEWEBM GOES18 colorized_ir_clouds-goes_wf_rss %today% 0
call :MAKEWEBM GOES18 overview-goes_wf_rss %today% 0

call :MAKEWEBM HIMA8 airmass-hima_f_rss %today% 0
call :MAKEWEBM HIMA8 colorized_ir_clouds-hima_f_rss %today% 0
call :MAKEWEBM HIMA8 overview-hima_f_rss %today% 0

GOTO :eof


:: Parameters: Sat (short name), composite-area, date (YYYYmmdd), reduce (0 or 1)
:MAKEWEBM

: That's where the frames come from
SET fradir=%prodir%\%1\frames
if %4==1 SET fradir=%prodir%\%1\images
:: That's where the webm movies go
SET movdir=%prodir%\%1\movies
:: That's where we build the movie
SET mfn=%tmpdir%\%1-%3-%2.webm
:: Number of intro (delay) frames
SET /A introfra=10
:: Number credits (trailer) frames
SET /A trailfra=25

SET /A num=0
del /f %tmpdir%\%2-*.jpg 2>NUL

:: The - in front of %2 is needed, otherwise 'overview' is mixed with 'ir_overview'!
FOR /f  %%G IN ('"dir %fradir%\%1-%today%*-%2.jpg /OD /B"') DO (call :SUBLNK %fradir%\%%G %tmpdir%\%2)

:: Add trailer with credits
FOR /f  "tokens=1,2" %%G IN ('"%identify% -ping -format "%%w %%h" %framen% 2>nul"') DO (call :HOKUSPOKUS %%G %%H)

SET number=000%num%
SET lastframe=%tmpdir%\%2-%number:~-4%.jpg
SET /A num+=1

:: Now annotate this last frame, put your text strings here
SET t0=Satpy Processing System (SPS) for EUMETCast V 4.1\n\n
SET t1=HW       axxiv (LittleBit PC), I7, 16GB RAM, 2013\n\n
SET t2=OS       Windows 10 PRO, 64Bit, (processing only!)\n\n
SET t3=Cron     All production chains are fully automated\n\n
SET t4=Python   PyTROLL/SatPy, https://pytroll.github.io\n\n
SET t5=Magick   https://imagemagick.org/script/index.php\n\n
SET t6=FFmpeg   https://ffmpeg.org, https://trac.ffmpeg.org\n\n
SET t7=Format   webp, webm, https://www.webmproject.org\n\n
SET t8=ADMIN    Ernst Lobsiger, member \"Old Farts\", 1952

%convert% %framen% -modulate 60,60 -background transparent -fill white -gravity west ^
-font %font% -pointsize %poin% -annotate +%offx%+0 "%t0%%t1%%t2%%t3%%t4%%t5%%t6%%t7%%t8%" %lastframe%

:: If we do add 30 links (-r 6) to lastframe. This makes the trailer stay 5 seconds.
FOR /l %%I IN (1, 1, %trailfra%) DO (call :SUBLNK %lastframe% %tmpdir%\%2)

IF %4==1 GOTO :filter
%ffmpeg% -y -r 6  -i %tmpdir%\%2-%%04d.jpg -c:v libvpx -pix_fmt yuv420p -crf 20 -b:v 2M %mfn%
# Move the movie when complete
move /Y %mfn%  %movdir%
del /f %tmpdir%\%2-*.jpg 2>NUL
GOTO :eof
:filter
%ffmpeg% -y -r 6  -i %tmpdir%\%2-%%04d.jpg -filter:v "scale=w=-1:h=1080" -c:v libvpx -pix_fmt yuv420p -crf 20 -b:v 2M %mfn%
# Move the movie when complete
move /Y %mfn%  %movdir%
del /f %tmpdir%\%2-*.jpg 2>NUL
GOTO :eof

:: Parameters: frame image n, link to image n
:SUBLNK
SET framen=%1
IF %num%==0 FOR /l %%N IN (1, 1, %introfra%) DO call :INTRODELAY %2
SET number=000%num%
mklink %2-%number:~-4%.jpg %framen%
SET /A num+=1
GOTO :eof

:: Show first frame a couple of times
:INTRODELAY
SET number=000%num%
mklink %1-%number:~-4%.jpg %framen%
SET /A num+=1
goto :eof


:: Originally a 3712 x 3712 Meteosat image got 640 caption pixels added at left:
:: This strip is 640/3712=0.1724 of the image height, CMD has no floating point
:: We get the full image width 3712+640=4352 and have to find the original width

:: Parameters: (full) width, hight
:HOKUSPOKUS
SET /A oriw=%1-(1724*%2)/10000
SET /A offx=%1-oriw
SET /A poin=oriw/35
SET /A offx=offx+2*poin
goto :eof




