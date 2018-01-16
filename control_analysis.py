'''
control_analysis.py

This code gets and maps variable data from wrfout files (in my case, control runs).
This has to be run in the directory with the control files.

Ryan Clare
October, 2017
University of Wisconsin-Madison
rclare2@wisc.edu
'''


#####################################################################################
#																					#
#							   Section 1 - Initialization							#
#																					#
#	Imports necessary libraries and indexes, prepares for gridspace to lat-lon 		#
#	conversion, and parses available outfile names for use in analysis.				#
#																					#
#####################################################################################


#Libraries Import#
#----------------#

from commands import *						#Library for executing Linux commands
from numpy import *							#Library for math
from matplotlib.pyplot import *				#Library for plotting
from mpl_toolkits.basemap import Basemap	#Library for map projections

#Lat/Lon Value Storage#
#---------------------#

#Store values for lat-lon/gridpoint conversion
f = open("/air/rclare/lonlat_index.txt", 'r')
llcontent = f.readlines()		
f.close()

m = linspace(0.0,142,143)					#Latitude linespace
n = linspace(0.0,208,209)					#Longitude linespace

#Conversion info arrays
x_grid, y_grid, longitude, latitude = [], [], [], []
longitude_grid, latitude_grid = [], []
long_store, lat_store = [], []

#Parse the conversion file
l = 0
for i in llcontent:
	mark1 = i.find(",")
	mark2 = i.find("|")
	mark3 = i[mark2:].find(",")
	x_grid.append(int(i[:mark1]))
	y_grid.append(int(i[mark1+2:mark2-1]))
	longitude.append(float64(i[mark2+2:mark2+mark3]))
	latitude.append(float64(i[mark2+mark3+2:-2]))	

#Convert Lat/Lon values to a grid 
l = 0
for i in range(len(m)):
	for j in range(len(n)):
		long_store.append(longitude[l])
		lat_store.append(latitude[l])
		l+=1		
	longitude_grid.append(asarray(long_store))
	latitude_grid.append(asarray(lat_store))
	long_store = []
	lat_store = []

#Store outfile names and times#
#-----------------------------#

ls_list = getoutput('ls wrfout*')
ls_list = ls_list.splitlines()
times=[]
for i in ls_list:
	times.append(i[16:])


#####################################################################################
#																					#
#							  Section 2 - Data Retrieval							#
#																					#
#	Writes ncl file to gather data from specified variables.						#
#																					#
#####################################################################################


#Create and execute NCL File#
#---------------------------#

#The contents of the ncl file
ncl_content = '\
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"					\n\
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"					\n\
begin																		\n\
  fList = systemfunc("ls -1 wrfout*")										\n\
  nFiles = dimsizes(fList) 													\n\
  do iFile = 0, nFiles - 1													\n\
	filename1 = sprinti("temp_snow%03d.txt",iFile)							\n\
	filename2 = sprinti("temp_var%03d.txt",iFile)							\n\
	filename3 = sprinti("temp_contr%03d.txt",iFile)							\n\
	a = addfile(fList(iFile),"r")											\n\
	p  = wrf_user_getvar(a,"pressure",-1)									\n\
	z  = wrf_user_getvar(a,"z",-1)											\n\
	snow   = wrf_user_getvar(a,"SNOWH",-1)									\n\
	var   = wrf_user_getvar(a,"slp",-1)										\n\
	;w = wrf_user_unstagger(var,var@stagger)								\n\
	z1_plane = wrf_user_intrp3d(z,p,"h",800.,0.,False)						\n\
	z2_plane = wrf_user_intrp3d(z,p,"h",500.,0.,False)						\n\
	z_plane = z2_plane - z1_plane											\n\
	;var_plane = wrf_user_intrp3d(w,p,"h",700.,0.,False)					\n\
	;WIND SPEED SECTION - COMMENT OUT IF NOT IN USE							\n\
	;u   = wrf_user_getvar(a,"U",-1)										\n\
	;ua = wrf_user_unstagger(u,u@stagger)									\n\
	;u_plane = wrf_user_intrp3d(ua,p,"h",300.,0.,False)						\n\
	;v   = wrf_user_getvar(a,"V",-1)										\n\
	;va = wrf_user_unstagger(v,v@stagger)									\n\
	;v_plane = wrf_user_intrp3d(va,p,"h",300.,0.,False)						\n\
	;c 	= (u_plane^2 + v_plane^2)^(1/2.)									\n\
	asciiwrite(filename1, snow)												\n\
	asciiwrite(filename2, var)												\n\
	asciiwrite(filename3, z_plane)											\n\
  end do																	\n\
end'

f = open("temp_ncl.ncl",'w')				#Creates local temporary ncl script
f.write(ncl_content)						#Writes above contents into file
f.close()

print "\n"
print "Executing NCL File..."
getoutput('ncl temp_ncl.ncl')				#Runs temporary ncl script

#Collecting the NCL data#
#-----------------------#

print "\n"
print "Reading Extracted Data..."
print "\n"
all_snow = []
for i in range(len(ls_list)):


	#Find the snow contour#
	#---------------------#

	mark = ls_list[i].find("wrfout_d01") + 11
	yr = ls_list[i][mark:mark+4]
	mn = ls_list[i][mark+5:mark+7]
	dy = ls_list[i][mark+8:mark+10]
	tim = ls_list[i][mark+11:]
	

	f = open("temp_snow%03d.txt" % i, 'r')		#Open file
	pcontent = f.readlines()					#Write each line into an array
	f.close()

	snow = zeros((len(m),len(n)))				#Temporary snow grid

	l = 0
	for k1 in range(len(m)):
		for k2 in range(len(n)):
			if float(pcontent[l]) > 0.02:		#Turn snow into a True/False at 2 cm
				snow[k1,k2] = 1.
			else:
				snow[k1,k2] = 0.
			l+=1
		all_snow.append(snow)


	#Find main variable data#
	#-----------------------#

	
	#1st Variable
	f = open("temp_var%03d.txt" % i, 'r')		#Open file
	pcontent = f.readlines()					#Write each line into an array
	f.close()
    
	var = zeros((len(m),len(n)))				#Temporary zeros variable grid
	
	l = 0
	for k1 in range(len(m)):
		for k2 in range(len(n)):
			var[k1,k2] = pcontent[l]			#Fill grid with data values
			l+=1		
			
	#2nd Variable
	f = open("temp_contr%03d.txt" % i, 'r')		#Open file
	pcontent = f.readlines()					#Write each line into an array
	f.close()
	
	contr = zeros((len(m),len(n)))				#Temporary zeros variable grid	
	
	l = 0
	for k1 in range(len(m)):
		for k2 in range(len(n)):
			contr[k1,k2] = pcontent[l]			#Fill grid with data values
			l+=1	


#####################################################################################
#																					#
#						 Section 3 - Calculations/Plotting							#
#																					#
#	Takes data and ananlyzes it.													#
#																					#
#####################################################################################

	
	#Initializing map#
	#----------------#
	
	fig = figure()
	map = Basemap(llcrnrlon=-120.,llcrnrlat=20.,urcrnrlon=-50.,urcrnrlat=50.,\
				rsphere=(6378137.00,6356752.3142),\
				resolution='l',projection='lcc',\
				lat_0=40.,lon_0=-98.,\
				lat_1=30.,lat_2=60.)
	
	#Draw geographical boundaries
	map.drawcoastlines(color='red',linewidth=0.75)
	map.drawstates(color='red',linewidth=0.75)
	map.drawcountries(color='red',linewidth=0.75)
	map.fillcontinents(color='black',lake_color='black')
	map.drawmapboundary(fill_color='black')
	
	#Create X-Y plane for contouring and filling on map
	X,Y = map(asarray(longitude_grid), asarray(latitude_grid))
	
	#1st Variable#
	#------------#
	
	#levels = linspace(250., 310., 13)							#Temperature levels (K)
	#levels = linspace(0., 8., 17)								#PV levels
	#levels = linspace(-20., 50., 15)							#Absolute vorticity levels
	#levels = linspace(40., 100., 13)							#Wind Speed levels
	#levels = linspace(-0.2, 0.2, 11)							#Vertical Wind Speed levels
	#var[abs(var) < 0.02] = float('nan')						#Drops low-end contours
	#CP = map.contourf(X,Y,var[:,:],levels)						#Creates contours with colors and data
	#cb = colorbar(CP)
	
	levels = linspace(700., 1200., 126)							#4 mb levels for SLP 
	cs = map.contour(X,Y,var,2,colors='c',linewidths=1.,levels=levels)
	clabel(cs, fmt="%1.0f", fontsize=8, inline=1)	
	
	#2nd Variable#
	#------------#
	
	levels = linspace(0.,12000.,241)							#50 m levels for thickness/height
	cs = map.contour(X,Y,contr,2,colors='y',linewidths=0.75,levels=levels)
	clabel(cs, fmt="%1.0f", fontsize=8, inline=1)
	
	#Snow Contour#
	#------------#
	
	cs = map.contour(X,Y,snow,2,colors='w',linewidths=2.,levels=[0.,1.])
	
	
	title('%s SLP [Blu] and 800-500 mb Height [Ylo] over Snow Line [Wht]' % times[i])
	print "(", i+1, "/", len(ls_list), ")"
	savefig('temp_plot%03d.jpg' % i)
	
print "\n"
print "Making GIF..."

getoutput('convert -loop 0 -delay 80 temp_plot* analysis/control.gif')

getoutput('rm temp_*')						#Remove temporary files
