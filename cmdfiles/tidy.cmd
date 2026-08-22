echo off
:: -----------------------------------------------------------------------------
:: Cron job to remove old EUMETCast products          (RSS frames most critical)
:: 
:: ForFiles (run as administrator) is used similar to find() (1) under GNU/Linux
:: It seems obvious that Microsoft takes (-) for (+) in the help ForFiles /? :-(
:: ForFiles is *SLOW*, do not run/schedule this at the same time with webm.cmd !
:: If you change the file layout of your system or add products adapt this too !
:: Integer numbers given to subroutines mean: Delete file if older than N days !
::
:: CH-3123 Belp, 2022/12/10           License GPL3            (c) Ernst Lobsiger
:: -----------------------------------------------------------------------------

:: The main directory
set datdir=D:\SPSdata

:: DEBUG is either con or nul
set DEBUG=con
set products=%datdir%\products
set overlays=%datdir%\overlays
set xtmpdirs=%datdir%\tmpdirs


:: Delete GEO frames/images/movies
call :GEOtrim MSG2   3 10 30
call :GEOtrim MSG3   3 10 30
call :GEOtrim MSG4   3 10 30
call :GEOtrim HIMA8  3 10 30
call :GEOtrim GOES16 3 10 30
call :GEOtrim GOES17 3 10 30
call :GEOtrim GOES18 3 10 30

:: Delete LEO images NIG/DAY
call :LEOtrim Aqua   30 30
call :LEOtrim Terra  30 30
call :LEOtrim MetopB 30 30
call :LEOtrim MetopC 30 30
call :LEOtrim MetopX 30 30
call :LEOtrim SNPP   30 30
call :LEOtrim NOAA20 30 30
call :LEOtrim NOAAX  30 30
call :LEOtrim FY3D   30 30
call :LEOtrim Sen3A  30 30
call :LEOtrim Sen3B  30 30
call :LEOtrim Sen3X  30 30

:: Delete GEO MSLP charts DWD/OPC/UKMO
call :MSLPtrim MSLP 30 30 30

:: Delete png MSLP overlays DWD/OPC/UKMO
call :OVERLAYtrim 5 5 5

:: Delete e.g. old remainders from different composite and area tests
call :TMPXtrim 10

:: All done!
goto :eof


:: -------------------------- Subroutines follow below ------------------------------  

:GEOtrim
  ForFiles /p %products%\%1\frames /m *.jpg /d -%2 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\images /m *.jpg /d -%3 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\movies /m *.webm /d -%4 /c "cmd /c del /q @file" 2>%DEBUG%
goto :eof

:MSLPtrim
  ForFiles /p %products%\%1\dwda  /m *.jpg /d -%2 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\dwdn  /m *.jpg /d -%2 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\dwdc  /m *.jpg /d -%2 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\dwdi  /m *.jpg /d -%2 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\opcae /m *.jpg /d -%3 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\opcaw /m *.jpg /d -%3 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\opcpe /m *.jpg /d -%3 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\opcpw /m *.jpg /d -%3 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\ukmos /m *.jpg /d -%4 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\ukmol /m *.jpg /d -%4 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\ukmox /m *.jpg /d -%4 /c "cmd /c del /q @file" 2>%DEBUG%
goto :eof

:LEOtrim
  ForFiles /p %products%\%1\NIG /m *.jpg /d -%2 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %products%\%1\DAY /m *.jpg /d -%3 /c "cmd /c del /q @file" 2>%DEBUG%
goto :eof

:OVERLAYtrim
  ForFiles /p %overlays%\dwda  /m *.png /d -%1 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %overlays%\dwdn  /m *.png /d -%1 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %overlays%\dwdc  /m *.png /d -%1 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %overlays%\dwdi  /m *.png /d -%1 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %overlays%\opcae /m *.png /d -%2 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %overlays%\opcaw /m *.png /d -%2 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %overlays%\opcpe /m *.png /d -%2 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %overlays%\opcpw /m *.png /d -%2 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %overlays%\ukmos /m *.png /d -%3 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %overlays%\ukmol /m *.png /d -%3 /c "cmd /c del /q @file" 2>%DEBUG%
  ForFiles /p %overlays%\ukmox /m *.png /d -%3 /c "cmd /c del /q @file" 2>%DEBUG%
goto :eof

:TMPXtrim
  ForFiles /p %xtmpdirs% /s /m *.png /d -%1 /c "cmd /c del /q @file" 2>%DEBUG%
goto :eof
