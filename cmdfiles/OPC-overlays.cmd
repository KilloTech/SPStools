@echo OFF
:: --------------------------------------------------------------
:: Script to download (colorized) OPC Ground Pressure Charts from
:: https://www.ocean.weather.gov and make PNG32 bc + wc overlays.
::
:: Overlays are 1776 pixels wide and 1562 pixels high (all areas)
::
:: Pressure lines + text black, rest color, needs fill_value=255
:: opcxy-bc-YYYYmmddHHMM.png, Mercator Projection,  6 hourly
:: Pressure lines + text white, rest color, needs fill_value = 0
:: opcxy-wc-YYYYmmddHHMM.png, Mercator Projection,  6 hourly
::
:: This script has to be scheduled 03:30 and every 6 hours later.
:: 30 3,9,15,21 * * * user script (30 3/6 * * * does not work !!)
::
:: CH-3123 Belp, 2022/12/10    License GPL3    (c) Ernst Lobsiger
::---------------------------------------------------------------

:: These two files are used to make 8 overlays for MSG4, GOES16, GOES18, Himawari-8 :
:: A_sfc_full_ocean_color.png, Atlantic, valid 1200, typically issued 14:39, 6 hourly
:: P_sfc_full_ocean_color.png, Pacific,  valid 1200, typically issued 15:05, 6 hourly
:: There is a 50° overlap of the resulting charts for both PacificW/E and AtlanticW/E

:: Regarding area definitions for opcae, opcaw, opcpe and opcpw see this discussion:
:: https://groups.google.com/g/pytroll/c/xTFZW1ptH7s     (you need my fixed PyCoast)

:: Windows finally comes with curl.exe and tar.exe. We use curl for download. If this doesn't
:: work for you then get a CLI wget.exe as fallback. I have used GNU Wget 1.15 built on mingw32
:: You can download this version from https://eternallybored.org/misc/wget   ... or ask David

:: We use flock and exit handlers under GNU/Linux Bash. There is no such thing under Windows CMD.
:: That said it's up to *you* to not start more than one instance of this script at the same time.

:: Two top directories
set toodir=C:\SPStools
set datdir=D:\SPSdata

:: ****************************************************
:: Touch this stuff below only if you know what you do!
:: ****************************************************

:: You must have write access to TMP_DIR (a working directory)
:: Downloaded files are deleted after overlays have been made!
set TMP_DIR=%datdir%\tmpdirs\xmslp
:: Processed overlays go in this base directory (must exist)
:: Sub directories opcae, opcaw, opcpe, opcpw (must exist)
set OVR_DIR=%datdir%\overlays
:: Windows 10 PRO 64Bit (ImageMagick portable)
set CONVERT=%toodir%\exefiles\convert.exe
:: WGET just as fall back, we now use curl.exe
set WGET=%toodir%\exefiles\wget.exe

set BASE_URL=https://ocean.weather.gov
set A_ocean=A_sfc_full_ocean_color.png
set P_ocean=P_sfc_full_ocean_color.png

:: If we cut the eastern Atlantic from the full_ocean image we have no lat labels!!
:: So I decided to add these labels with IM and also polish the rest of the labels.

:: Atlantic ocean western part        (overwrite OPC lat labels)
set lat60N="rectangle 1, 237,42, 259"& set txt60N="text  +5+255 '60N'"
set lat50N="rectangle 1, 627,42, 649"& set txt50N="text  +5+645 '50N'"
set lat40N="rectangle 1, 941,42, 963"& set txt40N="text  +5+959 '40N'"
set lat30N="rectangle 1,1213,42,1235"& set txt30N="text +5+1231 '30N'"
set lat20N="rectangle 1,1458,42,1480"& set txt20N="text +5+1476 '20N'"

:: Atlantic ocean eastern part (add missing lat labels in the middle)
set lam60N="rectangle 667, 237,708, 259"& set txm60N="text  +671+255 '60N'"
set lam50N="rectangle 667, 627,708, 649"& set txm50N="text  +671+645 '50N'"
set lam40N="rectangle 667, 941,708, 963"& set txm40N="text  +671+959 '40N'"
set lam30N="rectangle 667,1213,708,1235"& set txm30N="text +671+1231 '30N'"
set lam20N="rectangle 667,1458,708,1480"& set txm20N="text +671+1476 '20N'"

:: Atlantic ocean eastern and western part    (overwrite OPC lon labels)
set lon90W="rectangle  196,1534, 240,1557"& set txt90W="text  +200+1553 '90W'"
set lon80W="rectangle  418,1534, 462,1557"& set txt80W="text  +422+1553 '80W'"
set lon70W="rectangle  640,1534, 684,1557"& set txt70W="text  +644+1553 '70W'"
set lon60W="rectangle  862,1534, 906,1557"& set txt60W="text  +866+1553 '60W'"
set lon50W="rectangle 1084,1534,1128,1557"& set txt50W="text +1088+1553 '50W'"
set lon40W="rectangle 1305,1534,1349,1557"& set txt40W="text +1309+1553 '40W'"
set lon30W="rectangle 1527,1534,1571,1557"& set txt30W="text +1531+1553 '30W'"
set lon20W="rectangle 1749,1534,1793,1557"& set txt20W="text +1753+1553 '20W'"
set lon10W="rectangle 1971,1538,2015,1557"& set txt10W="text +1975+1553 '10W'"
set lon00W="rectangle 2198,1538,2242,1557"& set txt00W="text +2202+1553 '00W'"

:: Pacific ocean eastern and western part        (overwrite OPC lon labels)
set lon140E="rectangle   78,1534, 132,1557"& set txt140E="text   +83+1553 '140E'"
set lon150E="rectangle  300,1534, 354,1557"& set txt150E="text  +305+1553 '150E'"
set lon160E="rectangle  522,1534, 576,1557"& set txt160E="text  +527+1553 '160E'"
set lon170E="rectangle  744,1534, 798,1557"& set txt170E="text  +749+1553 '170E'"
set lon180E="rectangle  966,1534,1020,1557"& set txt180E="text  +979+1553 '180'"
set lon170W="rectangle 1188,1534,1242,1557"& set txt170W="text +1192+1553 '170W'"
set lon160W="rectangle 1409,1534,1463,1557"& set txt160W="text +1413+1553 '160W'"
set lon150W="rectangle 1631,1534,1685,1557"& set txt150W="text +1635+1553 '150W'"
set lon140W="rectangle 1853,1534,1907,1557"& set txt140W="text +1857+1553 '140W'"
set lon130W="rectangle 2075,1534,2129,1557"& set txt130W="text +2079+1553 '130W'"
set lon120W="rectangle 2297,1534,2351,1557"& set txt120W="text +2301+1553 '120W'"

:: Pacific ocean eastern and western part  (overwrite OPC lat labels)
set lpm60N="rectangle 954, 237,995, 259"& set tpm60N="text  +958+255 '60N'"
set lpm50N="rectangle 954, 627,995, 649"& set tpm50N="text  +958+645 '50N'"
set lpm40N="rectangle 954, 941,995, 963"& set tpm40N="text  +958+959 '40N'"
set lpm30N="rectangle 954,1213,995,1235"& set tpm30N="text +958+1231 '30N'"
set lpm20N="rectangle 954,1458,995,1480"& set tpm20N="text +958+1476 '20N'"


:: We start with images 2441 x 1600 pixels that are kind of overly colored.
:: Especially coast lines and text are not black and countours *ugly* brown.
:: Unfortunately there are two different palettes used on both Atlantic and
:: Pacific charts. Trying to use -fuzz 10% when changing colors didn't work.
:: Very rare, only found twice, #00514A is a dark green || front break mark.

del %TMP_DIR%\%A_ocean%
:: %WGET% --no-check-certificate -P %TMP_DIR% %BASE_URL%/%A_ocean%
:: YES, curl and tar is finally part of Microsoft Windows 10 :-)
curl --remote-time -o %TMP_DIR%\%A_ocean% %BASE_URL%/%A_ocean%
if not exist %TMP_DIR%\%A_ocean% (
  echo "ERROR: OPC %A_ocean% download failed!"
  goto :eof
)

:: Yes, this *must* stay on one line. It's the longest CMD statement I have ever written. And it works ;-) ...
for /f %%G in ('"PowerShell (Get-Date '1/1/1970').AddSeconds([long][math]::floor((Get-Date -Date (Get-ChildItem %TMP_DIR%\%A_ocean%).lastwritetime -uformat +%%s)/21600)*21600).ToString(\"yyyMMddHH\")"') do set OpcTime=%%G00


:: Atlantic ocean western part (GOES16)
set area=opcaw
%CONVERT% %TMP_DIR%\%A_ocean% -fill black -opaque #001c21 -fill black -opaque #001b23 ^
        ( %TMP_DIR%\%A_ocean% -fill black -opaque #00514a +transparent black ) -composite ^
        ( %TMP_DIR%\%A_ocean% -fill black -opaque #de7100 +transparent black ) -composite ^
        ( %TMP_DIR%\%A_ocean% -fill black -opaque #e16f00 +transparent black ) -composite ^
        ( %TMP_DIR%\%A_ocean% -fill black -opaque #0059ad +transparent black ) -composite ^
        ( %TMP_DIR%\%A_ocean% -fill black -opaque #005ab0 +transparent black ) -composite ^
        -fill white -stroke black -pointsize 18 +antialias ^
        -draw %lat60N% -draw %lat50N% -draw %lat40N% -draw %lat30N% ^
        -draw %lat20N% -draw %lon90W% -draw %lon80W% -draw %lon70W% ^
        -draw %lon60W% -draw %lon50W% -draw %lon40W% -draw %lon30W% ^
        -draw %lon20W% -fill black ^
        -draw %txt60N% -draw %txt50N% -draw %txt40N% -draw %txt30N% ^
        -draw %txt20N% -draw %txt90W% -draw %txt80W% -draw %txt70W% ^
        -draw %txt60W% -draw %txt50W% -draw %txt40W% -draw %txt30W% ^
        -draw %txt20W% -transparent white -crop 1776x1562+0+0 ^
        PNG32:%OVR_DIR%\%area%\%area%-bc-%OpcTime%.png

%CONVERT% %OVR_DIR%\%area%\%area%-bc-%OpcTime%.png -fill white -opaque black ^
        PNG32:%OVR_DIR%\%area%\%area%-wc-%OpcTime%.png

        
:: Atlantic ocean eastern part (MSG4)
set area=opcae
%CONVERT% %TMP_DIR%\%A_ocean% -fill black -opaque #001c21 -fill black -opaque #001b23 ^
        ( %TMP_DIR%\%A_ocean% -fill black -opaque #00514a +transparent black ) -composite ^
        ( %TMP_DIR%\%A_ocean% -fill black -opaque #de7100 +transparent black ) -composite ^
        ( %TMP_DIR%\%A_ocean% -fill black -opaque #e16f00 +transparent black ) -composite ^
        ( %TMP_DIR%\%A_ocean% -fill black -opaque #0059ad +transparent black ) -composite ^
        ( %TMP_DIR%\%A_ocean% -fill black -opaque #005ab0 +transparent black ) -composite ^
        -fill white -stroke black -pointsize 18 +antialias ^
        -draw %lam60N% -draw %lam50N% -draw %lam40N% -draw %lam30N% ^
        -draw %lam20N% -draw %lon60W% -draw %lon50W% -draw %lon40W% ^
        -draw %lon30W% -draw %lon20W% -draw %lon10W% -draw %lon00W% ^
        -fill black ^
        -draw %txm60N% -draw %txm50N% -draw %txm40N% -draw %txm30N% ^
        -draw %txm20N% -draw %txt60W% -draw %txt50W% -draw %txt40W% ^
        -draw %txt30W% -draw %txt20W% -draw %txt10W% -draw %txt00W% ^
        -transparent white -crop 1776x1562+665+0 ^
        PNG32:%OVR_DIR%\%area%\%area%-bc-%OpcTime%.png

%CONVERT% %OVR_DIR%\%area%\%area%-bc-%OpcTime%.png -fill white -opaque black ^
       PNG32:%OVR_DIR%\%area%\%area%-wc-%OpcTime%.png

del %TMP_DIR%\%P_ocean%
:: %WGET% --no-check-certificate -P %TMP_DIR% %BASE_URL%/%P_ocean%
:: YES, curl and tar is finally part of Microsoft Windows 10 :-)
curl --remote-time -o %TMP_DIR%\%P_ocean% %BASE_URL%/%P_ocean%
if not exist %TMP_DIR%\%P_ocean% (
  echo "ERROR: OPC %P_ocean% download failed!"
  goto :eof
)

:: Yes, this *must* stay on one line. It's the longest CMD statement I have ever written. And it works ;-) ...
for /f %%G in ('"PowerShell (Get-Date '1/1/1970').AddSeconds([long][math]::floor((Get-Date -Date (Get-ChildItem %TMP_DIR%\%P_ocean%).lastwritetime -uformat +%%s)/21600)*21600).ToString(\"yyyMMddHH\")"') do set OpcTime=%%G00


:: Pacific ocean western part (HIMA-8)
set area=opcpw
%CONVERT% %TMP_DIR%\%P_ocean% -fill black -opaque #001c21 -fill black -opaque #001b23 ^
        ( %TMP_DIR%\%P_ocean% -fill black -opaque #00514a +transparent black ) -composite ^
        ( %TMP_DIR%\%P_ocean% -fill black -opaque #de7100 +transparent black ) -composite ^
        ( %TMP_DIR%\%P_ocean% -fill black -opaque #e16f00 +transparent black ) -composite ^
        ( %TMP_DIR%\%P_ocean% -fill black -opaque #0059ad +transparent black ) -composite ^
        ( %TMP_DIR%\%P_ocean% -fill black -opaque #005ab0 +transparent black ) -composite ^
        -fill white -stroke black -pointsize 18 +antialias ^
        -draw %lpm60N%  -draw %lpm50N%  -draw %lpm40N%  -draw %lpm30N%  ^
        -draw %lpm20N%  -draw %lon140E% -draw %lon150E% -draw %lon160E% ^
        -draw %lon170E% -draw %lon180E% -draw %lon170W% -draw %lon160W% ^
        -draw %lon150W% -fill black ^
        -draw %tpm60N%  -draw %tpm50N%  -draw %tpm40N%  -draw %tpm30N%  ^
        -draw %tpm20N%  -draw %txt140E% -draw %txt150E% -draw %txt160E% ^
        -draw %txt170E% -draw %txt180E% -draw %txt170W% -draw %txt160W% ^
        -draw %txt150W% -transparent white -crop 1776x1562+0+0 ^
        PNG32:%OVR_DIR%\%area%\%area%-bc-%OpcTime%.png

%CONVERT% %OVR_DIR%\%area%\%area%-bc-%OpcTime%.png -fill white -opaque black ^
        PNG32:%OVR_DIR%\%area%\%area%-wc-%OpcTime%.png


:: Pacific ocean eastern part (GOES17, GOES18)
set area=opcpe
%CONVERT% %TMP_DIR%\%P_ocean% -fill black -opaque #001c21 -fill black -opaque #001b23 ^
        ( %TMP_DIR%\%P_ocean% -fill black -opaque #00514a +transparent black ) -composite ^
        ( %TMP_DIR%\%P_ocean% -fill black -opaque #de7100 +transparent black ) -composite ^
        ( %TMP_DIR%\%P_ocean% -fill black -opaque #e16f00 +transparent black ) -composite ^
        ( %TMP_DIR%\%P_ocean% -fill black -opaque #0059ad +transparent black ) -composite ^
        ( %TMP_DIR%\%P_ocean% -fill black -opaque #005ab0 +transparent black ) -composite ^
        -fill white -stroke black -pointsize 18 +antialias ^
        -draw %lpm60N%  -draw %lpm50N%  -draw %lpm40N%  -draw %lpm30N%  ^
        -draw %lpm20N%  -draw %lon170E% -draw %lon180E% -draw %lon170W% ^
        -draw %lon160W% -draw %lon150W% -draw %lon140W% -draw %lon130W% ^
        -draw %lon120W% -fill black ^
        -draw %tpm60N%  -draw %tpm50N%  -draw %tpm40N%  -draw %tpm30N%  ^
        -draw %tpm20N%  -draw %txt170E% -draw %txt180E% -draw %txt170W% ^
        -draw %txt160W% -draw %txt150W% -draw %txt140W% -draw %txt130W% ^
        -draw %txt120W% -transparent white -crop 1776x1562+665+0 ^
         PNG32:%OVR_DIR%\%area%\%area%-bc-%OpcTime%.png
%CONVERT% %OVR_DIR%\%area%\%area%-bc-%OpcTime%.png -fill white -opaque black ^
         PNG32:%OVR_DIR%\%area%\%area%-wc-%OpcTime%.png

:: All done!
