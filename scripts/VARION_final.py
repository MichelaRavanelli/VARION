#!/usr/bin/python
###########################
## --------------------- ##
#        varion.py        #
# 
# creation date: 23.10.2015
# Last modified: 09.03.2016
#
## --------------------- ##
###########################

## IMPORT MODULES AND CLASSES ##
import argparse  
#import datetime                     # Import datetime class
import os                           # Import os related functions 
#import sys
import glob
import numpy as np
import myRead as mR
import myObs as mO
import mySub_next_test as mS
import myFunc as mF
import test_next as tn

parser = argparse.ArgumentParser(prog="varion.py", description="varion.py is a script that process RINEX obs files" \
									  " and apply the VARION algorithm in order to obtain sTEC measuraments.\n" \
									  " author: Giorgio Savastano - giorgio.savastano@uniroma1.it")
									  
parser.add_argument("-staz", type=str, nargs='*', default="all", dest="stazName", help="This argument determines the station(s) will be processed." \
									  " By default, this parameter is set to process all the RINEX observation files in the working folder. ")
						   
parser.add_argument("-time", nargs='*', type=str, default="all", dest="analysisTime", 
										help="If no argument is given, the analysis is executed for " \
									  " all the time vector of the obs file." \
									  " Otherwise, the argument refers to the time for which the analysis"\
									  " should be performed and has to be in the format hh:min (GPS time)"\
									  "(e.g., 18:34 19:00)")
									  
parser.add_argument("-sat", type=int, nargs='*', default=0, dest="satNumber", help="This argument determines the satellite(s) will be considered." \
									  "By default, this parameter is set to process all the satellites in view for each epochs."\
									  "write just the PRN number (e.g., 1 5 23)")    

parser.add_argument('-brdc', dest="brdcOrb",  action='store_true')                  
									   
########################################################
## CLASSES ##
class myStation:
	""" This is the simple class to describe a GNSS station """
	def __init__ (self):
		self.name = ""
		self.oFile = ""        ## RINEX obs files
		self.GPSnFile = ""     ## RINEX GPS nav file
		self.GLOnFile = ""     ## RINEX GLO nav file
		self.skyFile  = ""     ## VADASE sky file
		self.brdcFile = ""
		self.process_able = False
	def VADASE_PROCESS_ABLE(self):
		""" This function checks if the station has the observation and sky
			file available in the processing folder. If this is the 
			case the "process_able" variable is set to True """
		if os.path.isfile(self.oFile) and os.path.isfile(self.GPSnFile):
			self.process_able = True
		elif os.path.isfile(self.brdcFile):
			self.process_able = True
########################################################
## VARIABLES ##                                       
#### Constant ####
L1 = 1.57542e9                           #HZ
L2 = 1.22760e9                           #HZ
A  = 40.308e16

c = 299792458.0                          # m/s

const_tec = ((L1**2)*(L2**2))/(A*(L1**2-L2**2))

h_iono = 350000.0

sats = np.asarray( ['G01','G02','G03','G04','G05','G06','G07','G08','G09','G10','G11','G12',\
					   'G13','G14','G15','G16','G17','G18','G19','G20','G21','G22','G23','G24',\
					   'G25','G26','G27','G28','G29','G30','G31'] )
######################################################## 
os.chdir('..')
main_dir = os.getcwd()
obs_dir  = main_dir + '/obs'
out_dir  = main_dir + '/outputs'
os.chdir('obs')

## PROGRAM STARTS ##
args = parser.parse_args()
print args 

if args.stazName == "all":
	stations = glob.glob('*.??o')
	stations.sort()
else:
	statio = args.stazName
	suffix = glob.glob(statio[0] + '*.??o')[0][4:]

	stations = [ sta + suffix for sta in statio ]
	stations.sort()
##########################################################   
#### METTERE POI OPZIONE PER IL FILE BRDC E IGS       ------- > IMPORTANTE 
if args.brdcOrb == True:
	brdc_file = glob.glob ( 'brdc' + '*.??n')
	print brdc_file

## COUNT HOW MANY NAVIGATION FILES ARE NOT AVAILABLE ##
myStationsProc = []                                                     # List of stations that will be processed

for sFile in stations:
		alreadyThere = False
		for station in myStationsProc:
			if sFile[0:4] == station.name:
				## The station is already in the list                   #
				## check if it has the observation and sky file         #
				## and if not assign them                               #
				if args.brdcOrb == True:
					station.brdcFile = brdc_file[0]
				if not station.oFile:
					station.oFile = sFile
				if not station.GPSnFile:
					sGPSnFile = sFile[:-1] + 'n' 
					if os.path.isfile(sGPSnFile):
						station.GPSnFile = sGPSnFile
				
				station.VADASE_PROCESS_ABLE()
							
				alreadyThere = True
				break
		## The station is not in the list
		
		if not alreadyThere:
			sStation = myStation()
			sStation.name = sFile[0:4]
			sStation.oFile = sFile
			sGPSnFile = sFile[:-1] + 'n' 
			if os.path.isfile(sGPSnFile):
				sStation.GPSnFile = sGPSnFile
			if args.brdcOrb == True:
				sStation.brdcFile = brdc_file[0]
			
			sStation.VADASE_PROCESS_ABLE()	
			myStationsProc.append(sStation)	

for i in myStationsProc:
		print i.name, i.oFile, i.GPSnFile, i.brdcFile, i.process_able 
##########################################################
if args.analysisTime != "all":
	 start = int(args.analysisTime[0][:2])*60.0*60.0 + int(args.analysisTime[0][3:5])*60.0   
	 stop  = int(args.analysisTime[1][:2])*60.0*60.0 + int(args.analysisTime[1][3:5])*60.0
	 print start, stop
	 
if args.satNumber == 0:
	sats_write = np.asarray( np.arange(1,32) )
	print sats
else:
	sats_write = np.asarray(args.satNumber)
	sats_write.sort()
	print sats_write

################################################################################
## EXECUTE VARION ##	

info_file = open(  "info.txt" , "w" )
for i in myStationsProc:
	if i.process_able:
		station = i.name
		rinex = i.oFile
		if args.brdcOrb == True:
			rinex_nav = brdc_file[0]
		else:
			rinex_nav = i.GPSnFile
		interval    = mR.interval(rinex)  
		xr,yr,zr    = mR.coord_xyz(rinex)
		lat_g,lon_g, h = mF.coord_geog(xr,yr,zr)
		
		info_file.write( str(station)+ "\t" + str(interval) + "\t" + str(lat_g) + "\t" + str(lon_g) + "\n"  )
				
		sIP = tn.coord_satellite( rinex_nav, i.oFile)

################################################################################
		lista_G = []
		sIP_G_list = []
		data_list = []
			
		for sa in xrange( len(sats) ):
				data   = mR.read_rinex( rinex )
				varion = mO.obs_sat( data[0], data[1], data[2], data[3], data[4], sats[sa])
				data_list.append( data )  
				lista_G.append( varion )
				sIP_sat = tn.track_sat( sIP, (sa+1) )
				phi_ipp, lambda_ipp, h_ipp = tn.coord_ipps( xr, yr, zr, sIP_sat[2], sIP_sat[3], sIP_sat[4], h_iono)

				sIP_G_list.append(  (sIP_sat[0],sIP_sat[1],phi_ipp,lambda_ipp)  )

		################################################################################
		### REMOVE THE OUTLAYER
		stec_list = []
		sod_list = []
		for i in range(0,len(lista_G)):
				mask = mF.no_outlayer_mask(lista_G[i][0] * const_tec / interval )  ## modify the treshold to remove the outlayer
				stec_list.append(  lista_G[i][0][mask] * const_tec / interval  ) 
				sod_list.append(   lista_G[i][2][mask]  )
		  
		################################################################################
		### POLINOMIAL INTERPOLATION OF THE DATA
		X_list = []
		Y_list = []
		mask_list = []
		p_list  = []
		interpo_list = []
	
		diff_list = []
		cum_list     = []

		for i in xrange( 1, 32):
				X = sod_list[i-1]
				Y = stec_list[i-1] 
				mask       = (X>=start) & (X<=stop)
				try:
					p        = np.poly1d(  np.polyfit(X[mask], Y[mask], 10)  )
					interpo = p(  X[mask]  )
			
					diff = Y[mask] - interpo  # residual
					cum = mF.integrate(  diff, interval  )
			
					X_list.append(X)
					Y_list.append(Y)
			
					mask_list.append(mask)
					p_list.append(p)
					interpo_list.append(interpo)
			
					diff_list.append(diff)
					cum_list.append(cum)
				except (TypeError, IndexError):
					X_list.append(0.0)
					Y_list.append(0.0)
			
					mask_list.append(0.0)
					p_list.append(0.0)
					interpo_list.append(0.0)
			
					diff_list.append(0.0)
					cum_list.append(0.0)       
		################################################################################
		### Create the .txt file
		################################################################################
	
		for i in sats_write:
				mask = (sIP_G_list[i-1][0] >= start) & (sIP_G_list[i-1][0] <= stop)
		
				f = open(out_dir + '/' + station+'_' + str(i) + '_test.txt', 'w')
				f.write('sow' + '\t' + '\t'  + '\t' + 'sTEC' + '\t' + '\t'+ '\t' 'lon' + '\t' + '\t'+ '\t' 'lat'+ '\n')
				try:
					for k in xrange(0,len(cum_list[i-1])):
						try:
							#### FIX DIFF OF TIME BETWEEN COORDINATES AND STEC (ONE COME FROM NAVIGATION FILE THE OTHER FROM OBS)
							## BUG FIXED  --> try with 30 s data
							inde = (np.where(X_list[i-1][mask_list[i-1]][k] ==  sIP_G_list[i-1][0][mask]) )
							f.write( str(sIP_G_list[i-1][0][mask][inde[0][0]]) + '\t' + '\t' + str(cum_list[i-1][k]) + '\t' + '\t' + \
										str(sIP_G_list[i-1][3][mask][inde[0][0]]) + '\t' + '\t' + str(sIP_G_list[i-1][2][mask][inde[0][0]]) +'\n')
						except IndexError:
							continue
				except TypeError or IndexError:
					continue
				f.close() 
info_file.close()  
	