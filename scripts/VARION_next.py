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
import myIono as mI
import mySub_next_test as mS
import myFunc as mF

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
                                       
########################################################
## CLASSES ##
class myStation:
    """This is the simple class to describe a GNSS station """
    def __init__(self):
        self.name = ""
        self.oFile = ""         ## RINEX obs files
        self.GPSnFile = ""      ## RINEX GPS nav file
        self.GLOnFile = ""      ## RINEX GLO nav file
        self.skyFile  = ""      ## VADASE sky file
        self.process_able = False
    def VADASE_PROCESS_ABLE(self):
        """ This function checks if the station has the observation and sky
            file available in the processing folder. If this is the case
            the "process_able" variable is set to True """
        if os.path.isfile(self.oFile) and os.path.isfile(self.skyFile):
            self.process_able = True
########################################################
## VARIABLES ##                                       
#### Constant ####
L1 = 1.57542e9                           #HZ
L2 = 1.22760e9                           #HZ
A  = 40.308e16

c = 299792458.0                          # m/s

const_tec = ((L1**2)*(L2**2))/(A*(L1**2-L2**2))

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
## COUNT HOW MANY NAVIGATION FILES ARE NOT AVAILABLE ##
myStationsProc = []                                                     # List of stations that will be processed

for sFile in stations:
    alreadyThere = False
    for station in myStationsProc:
        if sFile[0:4] == station.name:
            
            ## The station is already in the list                   #
            ## check if it has the observation and navigation file  #
            ## and if not assign them                              ##
            
            if not station.oFile:
                station.oFile = sFile
            if not station.GPSnFile:
                sSkyFile = sFile + '_L3_G_L1W+L2W_ALL.sky' 
                if os.path.isfile(sSkyFile):
                    station.skyFile = sSkyFile
            
            station.VADASE_PROCESS_ABLE()
                        
            alreadyThere = True
            break
    ## The station is not in the list
    
    if not alreadyThere:
        sStation = myStation()
        sStation.name = sFile[0:4]
        sStation.oFile = sFile
        sSkyFile = sFile + '_L3_G_L1W+L2W_ALL.sky' 
        if os.path.isfile(sSkyFile):
            sStation.skyFile = sSkyFile
        
        sStation.VADASE_PROCESS_ABLE()  
        myStationsProc.append(sStation) 

for i in myStationsProc:
    print i.name, i.oFile, i.skyFile, i.process_able 
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

for i in myStationsProc:
    if i.process_able:
        station = i.name
        lista_obs = glob.glob(station + "*.??o")
        lista_obs.sort()

        try:
                interval    = mI.interval(lista_obs[0])
                lat_g,lon_g = mI.location(lista_obs[0])
        except UnboundLocalError:
            ## Test debug, with function coord_geo written by me
            #lat_g,lon_g = mI.coord_geog(lista_obs[0])
                continue

        sIP = mS.subiono( i.skyFile, lat_g, lon_g )

        ################################################################################
        lista_G = []
        sIP_G_list = []
        for sa in sats:     
                lista_G.append(mI.iono(lista_obs, sa))
                sIP_G = mS.track(sIP, sa)
                sIP_G_list.append(sIP_G)

        #sIP_G_temp = mS.track_temp(sIP_G, tsunami - 100, tsunami + 8000, txt_file=True)
        ################################################################################
        ### REMOVE THE OUTLAYER
        for i in range(0,len(lista_G)):
                mask = mF.no_outlayer_mask(lista_G[i][0][1] * const_tec / interval )
                lista_G[i][0][1] = (lista_G[i][0][1][mask] * const_tec / interval ) 
                lista_G[i][0][0] = lista_G[i][0][0][mask]
          
        ################################################################################
        ### POLINOMIAL INTERPOLATION OF THE DATA
        X_list = []
        Y_list = []
        mask_list = []
        p08_list  = []
        interpo_08_list = []
    
        diff_08_list = []
        cum_list     = []

        for i in xrange( 1, 32):
                X = lista_G[i-1][0][0]
                Y = lista_G[i-1][0][1] 
                mask       = (X>=start) & (X<=stop)
                try:
                    p08        = np.poly1d(np.polyfit(X[mask], Y[mask], 8))
                    interpo_08 = p08(X[mask])
            
                    diff_08 = Y[mask] - interpo_08  # residual
                    cum = mF.integrate(diff_08, interval)
            
                    X_list.append(X)
                    Y_list.append(Y)
            
                    mask_list.append(mask)
                    p08_list.append(p08)
                    interpo_08_list.append(interpo_08)
            
                    diff_08_list.append(diff_08)
                    cum_list.append(cum)
                except (TypeError, IndexError):
                    X_list.append(0.0)
                    Y_list.append(0.0)
            
                    mask_list.append(0.0)
                    p08_list.append(0.0)
                    interpo_08_list.append(0.0)
            
                    diff_08_list.append(0.0)
                    cum_list.append(0.0)       
        ################################################################################
        ### Create the .txt file
        ################################################################################
    
        for i in sats_write:
                mask = (sIP_G_list[i-1][0] >= start) & (sIP_G_list[i-1][0] <= stop)
        
                f = open(out_dir + '/' + station+'_' + str(i) + '_test.txt', 'w')
                f.write('sow' + '\t' + '\t'  + '\t' + 'sTEC' + '\t' + '\t'+ '\t' 'lon' + '\t' + '\t'+ '\t' 'lat'+ '\t'  + '\t'+ '\t' 'azi'+ '\t'  + '\t'+ '\t' 'ele' +'\n')
                try:
                    for k in xrange(0,len(cum_list[i-1])):
                        try:
                            #### FIX DIFF OF TIME BETWEEN COORDINATES AND STEC (ONE COME FROM NAVIGATION FILE THE OTHER FROM OBS)
                            ## BUG FIXED  --> try with 30 s data
                            inde = (np.where(X_list[i-1][mask_list[i-1]][k] ==  sIP_G_list[i-1][0][mask]) )
                            f.write( str(sIP_G_list[i-1][0][mask][inde[0][0]]) + '\t' + '\t' + str(cum_list[i-1][k]) + '\t' + '\t' + \
                                        str(sIP_G_list[i-1][3][mask][inde[0][0]]) + '\t' + '\t' + str(sIP_G_list[i-1][2][mask][inde[0][0]]) + \
                                        '\t' + '\t' + str(sIP_G_list[i-1][5][mask][inde[0][0]]) + '\t' + '\t' + str(sIP_G_list[i-1][4][mask][inde[0][0]]) +'\n')
                        except IndexError:
                            continue
                except TypeError or IndexError:
                    continue
                f.close()   
    