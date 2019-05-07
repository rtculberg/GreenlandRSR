Calibration flight lines for each season from 2011-2016. Each flight line is adjacent to one of the near-surface density logs in the SurfaceDensity directory.

The density# designator at the end of the file name tells you which density log is adjacent to that flight line. Note that density logs 4 and 5 were not in a dry
snow zone, so I didn't process any flight lines in that area. The flight line for the density 2 log need a bunch of metadata rewritten to process (which takes about 
18 hours...) so I skipped that line since there is already another calibration line for 2011. 

In the 2015 and 2016 flight lines the SNR in the unfocused data is too low to detect the bed (the bed is barely trackable even in the SAR processed data), so the ice
thickness, bed amplitude, and SNR fields are set to the NO DATA value of -9999. 