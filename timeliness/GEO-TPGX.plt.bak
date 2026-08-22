#
# gnuplot -e "sat='$sat'; dat1='$dat1'; dat2='$dat2'; mint=$mint; maxt=$maxt; \
#           minp=$minp; maxp=$maxp; chann='$chann'; color='$color'" GEO-TPGX.plt
#

reset
myfont14='/usr/share/fonts/truetype/noto/NotoMono-Regular.ttf,14'
myfont16='/usr/share/fonts/truetype/noto/NotoMono-Regular.ttf,16'

set term gif size 800,512 linewidth 2 font 'Helvetica,15'
set title sprintf("Timeliness of %s data from %s to %s", sat, dat1, dat2)

set label "EUMETCast" at scr 0.78, 0.81 font myfont14
set label chann at scr 0.78, 0.75 font myfont14
set label sprintf("mint=%3dmin", mint) at scr 0.78, 0.69 font myfont14
set label sprintf("maxt=%3dmin", maxt) at scr 0.78, 0.63 font myfont14

n=maxp-minp #number of intervals
width=(maxp-minp)/n #interval width (1 minute)
#function used to map a value to the intervals
hist(x,width)=width*floor(x/width)+width/2.0
# set term png  #output terminal and file
set output sprintf("/home/eumetcast/SPSdata/products/%s-timeliness.png", sat)
set xrange [minp:maxp]
set yrange [0:]
#to put an empty boundary around the
# data inside an autoscaled graph.
set xtics minp,(maxp-minp)/5, maxp
set boxwidth width*0.9
set style fill solid 0.5 #fillstyle
set tics out nomirror
set xlabel "Slot time to file on HDD = timeliness [min]"
set ylabel "number of files"
# count and plot
plot "timeliness.txt" u (hist($1,width)):(1.0) smooth freq w boxes lc rgb color notitle
