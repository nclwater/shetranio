import matplotlib.pyplot as plt
import numpy as np
import h5py
import os
import datetime


#using HDF file produces Time Series of discharge at specifed Shetran channel numbers
#++++++++++++++++++++++++++++++++++++++++
#THINGS TO CHANGE

# path to h5 file
h5File = "output_Wansbeck_at_Mitford_shegraph.h5"


# name of HDF file output group
HDFgroup = '4 ovr_flow'

#outfile location
outfilefolder = '2-output-overland-flow-timeseries'

#points that you want time series data for
timeseriesLocations= 'overland-flow-locations.txt'

# CHANGE ME to start date of simulation period (Y, m, d, h, min)
day1 = datetime.datetime(1992, 1, 1, 0, 0) 

#++++++++++++++++++++++++++++++++++++++++


def getColRowLocation():

    tgroup    = '/CONSTANTS'
    tsubgroup = 'number'



    group = fh5[tgroup]
    #print group

    for subgroup in group: # iterate over subgroups
        #print subgroup
        if tsubgroup in subgroup: 
            #print 'found required subgroup: ' , subgroup

            val = group[subgroup]
            ColRowLocation1 = val[:,:,5]
            ColRowLocation2 = val[:,:,6]
            ColRowLocation3 = val[:,:,7]
            ColRowLocation4 = val[:,:,8]

  
    return np.array(ColRowLocation1),np.array(ColRowLocation2),np.array(ColRowLocation3),np.array(ColRowLocation4)

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
            Elevation1 = val[:,:,5]
            Elevation2 = val[:,:,6]

  
    return np.array(Elevation1),np.array(Elevation2)



def getTimeSeriesFromPoint(i,HDFgroup):

    tgroup    = '/VARIABLES'
    tsubgroup = HDFgroup


    group = fh5[tgroup]

    for subgroup in group: # iterate over subgroups
        if tsubgroup in subgroup: 
            #print 'found required subgroup: ' , subgroup
            val = group[subgroup + '/' + 'value']

            # data[channel number:face:time]
            # use i-1 as i starets at 0
            data = val[i-1,:,:]
 
    return data

def getOvertimes(HDFgroup):

    tgroup    = '/VARIABLES'
    tsubgroup = HDFgroup


    group = fh5[tgroup]

    for subgroup in group: # iterate over subgroups
        if tsubgroup in subgroup: 
            #print 'found required subgroup: ' , subgroup
            times = group[subgroup + '/' + 'time']
            Overtimes = times[:]


    return Overtimes

def timeseriesplot(psltimes,data,Npoints,OverlandLoc,ElevationLink):

    plotlabel= np.empty(Npoints, dtype=object)
    fig = plt.figure(figsize=[12.0, 5.0])
    plt.subplots_adjust(bottom=0.2,right=0.75)
    ax = plt.subplot(1, 1, 1)
    i=0
    while i<Npoints:
        if ElevationLink[i]!=-999:
            plotlabel[i]='River Link= %4s'%str(int(OverlandLoc[i]))+' Elev= %7.2f m'%ElevationLink[i]
            #plot m below ground
            ax.plot(psltimes,data[i,:],label=plotlabel[i])
            #plot absolute elevation
            #ax.plot(psltimes,elevation[i]-data[i,:],label=plotlabel[i])
        i+=1
    #plot m below ground
    ax.set_ylabel('Discharge (m$^3$/s)')
    plt.xticks(rotation=70)
    legend = ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.,prop={'size':8})
    plt.savefig(outfilefolder+'/'+'Discharge-timeseries.png')
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
    for line in locations:
        x[i] = line
        i+=1
    return x

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# make folder for graphs and outputs
if not os.path.exists(outfilefolder):
    os.mkdir(outfilefolder)

#number of points (Npoints) in tuime series file
locations=open(timeseriesLocations,"r")
Npoints=getTimeSeriesNpoints(locations)


#go back to start of file and get locations
locations.seek(0)
OverlandLoc=getTimeSeriesLocation(locations,Npoints)

fh5 = h5py.File(h5File,'r')


#find location and elevation of each channel link
#river links in Shetran flow along the edge of the grid squares. The number starts at the bottom left then considers each row in turn going upwards.
# There are north-south and east-west channels
ColRowLocation1,ColRowLocation2,ColRowLocation3,ColRowLocation4 = getColRowLocation()
Elevation1,Elevation2 = getElevations()
ElevationLink=np.zeros(shape=(Npoints))
i=0
while i<Npoints:
    p1= np.where(ColRowLocation1 == int(OverlandLoc[i]))
    p2= np.where(ColRowLocation2 == int(OverlandLoc[i]))
    p3= np.where(ColRowLocation3 == int(OverlandLoc[i]))
    p4= np.where(ColRowLocation4 == int(OverlandLoc[i]))
    if p1[0]>0:
        ElevationLink[i]=Elevation1[p1]
        print str(int(OverlandLoc[i])) +' is a E-W channel on column '+ str(p1[1])[1:-1]+' between rows '+ str(p3[0])[1:-1]+ ' and '+ str(p1[0])[1:-1]+ ' with elevation = '+ str(Elevation1[p1])[1:-1]
    elif p2[0]>0:
        ElevationLink[i]=Elevation2[p2]
        print str(int(OverlandLoc[i])) +' is a N-S channel on row '+ str(p2[0])[1:-1]+' between columns '+ str(p2[1])[1:-1]+ ' and  '+ str(p4[1])[1:-1]+' with elevation = '+ str(Elevation2[p2])[1:-1]
    else:
        ElevationLink[i]=-999
        print str(int(OverlandLoc[i])) +' is not a Shetran link number'
    i+=1

# get times of output. ntimes is the final time
Overtimes=getOvertimes(HDFgroup)
dimstime = Overtimes.shape
ntimes = dimstime[0]

#setup a datetime array. there must be a better way than this
datetimes = np.array([day1 + datetime.timedelta(hours=i) for i in xrange(ntimes)])
i=0
while i<ntimes:
    datetimes[i]= day1 + datetime.timedelta(hours=int(Overtimes[i]))
    i+=1

#get the time series data
#discharge is specifed at 4 faces. We want the maximum absolute discharge
data=np.zeros(shape=(Npoints,4,ntimes))
data2=np.zeros(shape=(Npoints,ntimes))
i=0
while i<Npoints:
    if ElevationLink[i]!=-999:
        data[i,:,:]=getTimeSeriesFromPoint(OverlandLoc[i],HDFgroup)
    i+=1
for i in range (0,Npoints):
    for j in range (0,ntimes):
        data2[i,j]=np.amax(abs(data[i,:,j]))

# time series plots. 
print 'time series plot'
timeseriesplot(datetimes,data2,Npoints,OverlandLoc,ElevationLink)



