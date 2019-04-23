Text File Naming Convention:

	[Geographic Area Code]_[Collection Date]_[CReSIS Flight Segment #]_[CReSIS Frame #].txt
	
	Geographic Area Codes:
		NOG - Northwest Outlet Glaciers
		CC - Camp Century

	Collection Date (YYYYMMDD)
		Date on which that flight line was recorded.
	
	CReSIS Flight Segment Number
		CReSIS changes the flight segment number everytime the radar parameters are changed, or
		the radar is turned off for some reason. Records from the same date and flight segment
		are directly radiometrically comparable.
	
	CReSIS Frame Number
		For ease of processing, CReSIS then breaks the segments up into frames which correspod to 
		roughly 50 kilometers of flight line. The frame number always increments in order along the
		flight line. So for example, the files with frames 41, 42, and 43 from the same date and flight
		segment would constitute a contiguous 150km radar profile. 

		
Text files are comma-separated and contain nine (9) data columns:

Column      Field                    Units                 Data Type                                Notes
1           Latitude	             Decimal degrees       Double precision floating point          WGS-84 geodetic coordinate
2           Longitude	             Decimal degrees       Double precision floating point          WGS-84 geodetic coordinate
3           Roll Angle	             Radians               Double precision floating point
4           Distance to Surface      Meters                Double precision floating point          As measured from GPS antenna phase center
5           Surface Amplitude - I    Volts                 Double precision floating point          Real component of surface echo amplitude.
6           Surface Amplitude - Q    Volts                 Double precision floating point          Imaginary component of surface echo amplitude.
7           Ice Thickness            Meters                Double precision floating point          Converted from two-way travel time using a constant permittivity of 3.17
8           Bed Amplitude - I        Volts                 Double precision floating point          Real component of bed echo amplitude, usually in scientific notation (eg. 1e-08) due to small values  
9           Bed Amplitude - Q        Volts                 Double precision floating point          Imaginary component of bed echo amplitude, usually in scientific notation (eg. 1e-08) due to small values  
10          Bed Pick SNR             dB                    Double precision floating point          10*log10(P_bed/P_noise)

The accompanying JPEG files are low-quality images of the SAR focused radargrams for each flight frame 
(file naming convention matches the text file naming convention) to give a quick sense of the topography 
and glacial conditions in each area. 

Surface and Bed Picking Methodology:

	Surface:
		In the initial pass, the script picks the first amplitude maximum after the feedthrough. To avoid 
		picking strong near-surface scattering anomalies or clutter peaks, the script then runs a second 
		pass. For any trace where the inital surface pick deviates by more than one range bin from surface 
		pick in the previous trace, a new surface pick is selected which is the first peak within a 30 range
		bin window of the surface that exceeds some threshold (usually within 15 dB of the mean surface 
		amplitude).
	
	Bed:
		The bed picking algorithm is a bit more experimental. In the pulse compressed data, the bed is rarely
		clearly defined, unless it is quick flat. Therefore, script initially picks the bed surface from a SAR
		processed image of the same scene by selecting the first amplitude maximum after some manually defined 
		offset in the basal echo free zone. These bed picks are then co-registered to the pulse compressed data 
		for the scene. Because the existing SAR processed data has been significantly downsampled in azimuth 
		(typically there are about 100 traces in the pulse compressed data for every trace in the SAR data), 
		the script fills in the gaps between the SAR bed picks by picking the trace maximum in a window whose 
		upper and lower depth bounds are defined by the previous and next SAR bed pick. 