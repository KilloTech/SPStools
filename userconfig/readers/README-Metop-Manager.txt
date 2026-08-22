Some Windows users want to preprocess Metop GDS raw data with David's Metop Manager.
For unknown reasons the seemingly exact same version of this program with the same
configuration can pass the EUMETCast segment data decompressed (ending *.eps-glb)
or compressed as distributed (ending *.bz2). The respective Satpy reader expects
the data decompressed but a suffix *.eps-glb is not in the list of possible names.

SPS 4.x normally decompresses data if necessary and just cuts off the suffix *.bz2
from the filenames. It also accepts decompressed data that use the same file naming.


To make SPS 4.x accept decompressed Metop data with David's naming *.eps-glb do this:
-------------------------------------------------------------------------------------

1) In this directory rename the file "avhrr_l1b_eps.yaml.txt" to "avhrr_l1b_eps.yaml".

   Be aware that this file now takes precedence over the original in .../satpy/etc/readers.
   In the very unlikely case that the original will be updated with Satpy later, your copy
   will not be changed. Then you have to recopy the original here and add David's naming.

2) Adapt LEOstuff.py accordingly (as date and time positions are counted from the end):

Look for these lines for Metop-B:

                return False, 'AVHR_xxx_1B_M01_', -51, -37, '%Y%m%d%H%M%S', '', 'Z', 90
                # return False, 'AVHR_xxx_1B_M01_', -59, -45, '%Y%m%d%H%M%S', '', 'Z.eps-glb', 90

Look for these lines for Metop-C:

                return False, 'AVHR_xxx_1B_M03_', -51, -37, '%Y%m%d%H%M%S', '', 'Z', 90
                # return False, 'AVHR_xxx_1B_M03_', -59, -45, '%Y%m%d%H%M%S', '', 'Z.eps-glb', 90

Then comment/uncomment those to (*BE SURE TO USE THE SAME INDENTATION*):

                # return False, 'AVHR_xxx_1B_M01_', -51, -37, '%Y%m%d%H%M%S', '', 'Z', 90
                return False, 'AVHR_xxx_1B_M01_', -59, -45, '%Y%m%d%H%M%S', '', 'Z.eps-glb', 90

                # return False, 'AVHR_xxx_1B_M03_', -51, -37, '%Y%m%d%H%M%S', '', 'Z', 90
                return False, 'AVHR_xxx_1B_M03_', -59, -45, '%Y%m%d%H%M%S', '', 'Z.eps-glb', 90



Now SPS 4.x should work with setting "decomp=True" in the respective Metop LEOscripts. Good luck!
