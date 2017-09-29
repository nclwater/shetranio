import matplotlib.pyplot as plt
import numpy as np
import h5py
import os
import datetime


#using HDF file produces Time Series of phreatic surface depth at timeseriesLocations
#++++++++++++++++++++++++++++++++++++++++
#THINGS TO CHANGE

# path to h5 file
h5File = "output_76008_shegraph.h5"


# name of HDF file output group
HDFgroup = '2 ph_depth'

#outfile location
outfilefolder = '3-output-WaterTable-timeseries'

#points that you want time series data for
timeseriesLocations= 'WaterTable-timeseries-locations.txt'

# CHANGE ME to start date of simulation period (Y, m, d, h, min)
day1 = datetime.datetime(1992, 1, 1, 0, 0) 

#++++++++++++++++++++++++++++++++++++++++


def getElevations():

    tgroup    = '/CONSTANTS'
    tsubgroup = 'surf_elv'



    group = fh5[tgroup]
    #print group

    for subgroup in group: # iterate over subgroups
        #print subgroup
        if tsubgroup in subgroup: 
            #print 'found required subgroup: ' , subgroup

            val = group[subgroup]
            dims = val.shape
             #Shetran adds extra column and row around grid. Only need dem in normal grid
            nrows = dims[0]-1
            ncols = dims[1]-1
            dem = val[0:nrows-1,0:ncols-1,0]

  
    return np.array(dem),nrows,ncols



def getTimeSeriesFromPoint(j,i,HDFgroup):

    tgroup    = '/VARIABLES'
    tsubgroup = HDFgroup


    group = fh5[tgroup]

    for subgroup in group: # iterate over subgroups
        if tsubgroup in subgroup: 
            #print 'found required subgroup: ' , subgroup
            val = group[subgroup + '/' + 'value']

            # data[nrows:ncols:time] ie [j,i,:]
            data = val[j,i,:]
 
    data = [round(m,2) for m in data]
    return data

def getpsltimes(HDFgroup):

    tgroup    = '/VARIABLES'
    tsubgroup = HDFgroup


    group = fh5[tgroup]

    for subgroup in group: # iterate over subgroups
        if tsubgroup in subgroup: 
            #print 'found required subgroup: ' , subgroup
            times = group[subgroup + '/' + 'time']
            psltimes = times[:]


    return psltimes

def timeseriesplot(psltimes,data,Npoints,row,col,elevation):

    plotlabel= np.empty(Npoints, dtype=object)
    fig = plt.figure(figsize=[12.0, 5.0])
    plt.subplots_adjust(bottom=0.2,right=0.75)
    ax = plt.subplot(1, 1, 1)
    i=0
    while i<Npoints:
        if elevation[i]!=-1:
            plotlabel[i]='Col='+str(int(col[i]))+' Row='+str(int(row[i]))+' Elev= %7.2f m'%elevation[i]
            #plot m below ground
            ax.plot(psltimes,data[i,:],label=plotlabel[i])
            #plot absolute elevation
            #ax.plot(psltimes,elevation[i]-data[i,:],label=plotlabel[i])
        i+=1
    #plot m below ground
    ax.set_ylabel('Water Table Depth (m below ground)')
    #plot absolute elevation
    #ax.set_ylabel('Phreatic Surface Level (m ASl)')
    plt.xticks(rotation=70)
    plt.gca().invert_yaxis()
    legend = ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.,prop={'size':8})
    plt.savefig(outfilefolder+'/'+'watertable-timeseries.png')
    plt.close()

    return

def getTimeSeriesNpoints(locations):
    # skip over the headers
    locations.readline()
    i=0
    for line in locations:
        line.rstrip().split(",")
        i+=1
    return i

def getTimeSeriesLocation(locations,Npoints):
    # skip over the headers
    locations.readline()
    i=0
    x=np.zeros(shape=(Npoints))
    y=np.zeros(shape=(Npoints))
    for line in locations:
        x[i], y[i] = line.rstrip().split(",")
        i+=1
    return x,y

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# make folder for graphs and outputs
if not os.path.exists(outfilefolder):
    os.mkdir(outfilefolder)

#number of points (Npoints) in tuime series file
locations=open(timeseriesLocations,"r")
Npoints=getTimeSeriesNpoints(locations)


#go back to start of file and get locations
locations.seek(0)
col,row=getTimeSeriesLocation(locations,Npoints)

fh5 = h5py.File(h5File,'r')
#dem is row number(from top), column number
dem,nrows,ncols = getElevations()

#elevations correspond to the row number and column number in hdf file
elevation=np.zeros(shape=(Npoints))
i=0
while i<Npoints:

    elevation[i]=dem[int(row[i]),int(col[i])]
    if elevation[i]==-1:
        print 'column ',int(col[i]),' row ',int(row[i]),' outside of catchment'

    i+=1


# get times of output. ntimes is the final time
psltimes=getpsltimes(HDFgroup)
dimstime = psltimes.shape
ntimes = dimstime[0]

#setup a datetime array. there must be a better way than this
datetimes = np.array([day1 + datetime.timedelta(hours=i) for i in xrange(ntimes)])
i=0
while i<ntimes:
    datetimes[i]= day1 + datetime.timedelta(hours=int(psltimes[i]))
    i+=1

#get the time series data
data=np.zeros(shape=(Npoints,ntimes))
i=0
while i<Npoints:
    data[i,:]=getTimeSeriesFromPoint(row[i],col[i],HDFgroup)
    i+=1

# time series plots. 
print 'time series plot'
timeseriesplot(datetimes,data,Npoints,row,col,elevation)



