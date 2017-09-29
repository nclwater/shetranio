import matplotlib.pyplot as plt
import numpy as np
import h5py
import os

#using HDF file produces 2d plots of phreatic surface depth at regular timesteps
#++++++++++++++++++++++++++++++++++++++++
#THINGS TO CHANGE

# path to h5 file
h5File = "output_Wansbeck_at_Mitford_shegraph.h5"

# time interval between 2d plots. A value of 365 produces a plot every 365 output timesteps
timeinterval=1

#starting time for 2d plot. A value of 10 starts at output timestep 10
time=0

# name of HDF file output group
HDFgroup = '2 ph_depth'

#outfile location
outfilefolder = '4-output-WaterTable-2dplots'

#++++++++++++++++++++++++++++++++++++++++



#assume grid size is the same everywhere (this is not necessarily true but is usual)
def getGridSize():    

    tgroup    = '/CONSTANTS'
    tsubgroup = 'grid_dxy'



    group = fh5[tgroup]
    #print group

    for subgroup in group: # iterate over subgroups
        #print subgroup
        if tsubgroup in subgroup: 
            #print 'found required subgroup: ' , subgroup

            val = group[subgroup]
            Gridsize=np.nanmax(val)
            #print Gridsize

  
    return Gridsize

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
            dem = val[1:nrows,1:ncols,0]

  
    return np.array(dem),nrows,ncols



def getpsl(t,nrows,ncols,HDFgroup):

    tgroup    = '/VARIABLES'
    tsubgroup = HDFgroup


    group = fh5[tgroup]

    for subgroup in group: # iterate over subgroups
        if tsubgroup in subgroup: 
            #print 'found required subgroup: ' , subgroup
            val = group[subgroup + '/' + 'value']

            # inputs[nrows:ncols:time] ie [j,i,:]
            data = val[1:nrows,1:ncols,t]
 
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

def TwoDPlot(time,ntimes,nrows,ncols,minpsl,maxpsl,GridSize,timeinterval,HDFgroup,outfilefolder):
    while time < ntimes:

        fig = plt.figure(figsize=[12.0,12.0])
        h5datapsl2d=getpsl(time,nrows,ncols,HDFgroup)
        h5datapsl2d[h5datapsl2d==-1.0]=np.nan

        ax = plt.subplot(1, 1, 1)
        ax.axis([0, GridSize*ncols, 0, GridSize*nrows])
        ax.set_xlabel('Distance(m)')
        ax.set_ylabel('Distance(m)')
        cax = ax.imshow(h5datapsl2d, extent=[0,GridSize*ncols,0,GridSize*nrows],interpolation='none',vmin=minpsl, vmax=maxpsl, cmap='Blues_r')
        #cbar = fig.colorbar(cax,ticks=[-1,0,1,2],fraction=0.04, pad=0.10)
        cbar = fig.colorbar(cax,fraction=0.04, pad=0.10)
        plt.subplots_adjust(wspace=0.4)

        fig.suptitle("Water Table depth - meters below ground. Time = %7.0f hours"%psltimes[time], fontsize=14, fontweight='bold')

        plt.savefig(outfilefolder+'/'+'WaterTable-2d-time'+str(time)+'.png')
        plt.close()

        time+=timeinterval
    return


def maxminpsl(nrows,ncols,ntimes,timeinterval):
    minpsl=99999.0
    maxpsl=-99999.0
    time=0
    while time < ntimes:
        h5datapsl2d=getpsl(time,nrows,ncols,HDFgroup)
        h5datapsl2d[h5datapsl2d==-1.0]=np.nan
        minpsl=min(minpsl,np.nanmin(h5datapsl2d))
        maxpsl=max(maxpsl,np.nanmax(h5datapsl2d))
        #print minpsl,maxpsl

        time+=timeinterval
    return minpsl,maxpsl

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# make folder for graphs and outputs
if not os.path.exists(outfilefolder):
    os.mkdir(outfilefolder)


fh5 = h5py.File(h5File,'r')
dem,nrows,ncols = getElevations()


GridSize=getGridSize()

# get times of output. ntimes is the final time
psltimes=getpsltimes(HDFgroup)
dimstime = psltimes.shape
ntimes = dimstime[0]

# obtain max and min psl
minpsl,maxpsl=maxminpsl(nrows,ncols,ntimes,timeinterval)

# 2d plots. The numbers produced depend on the time interval
print '2d plot'
TwoDPlot(time,ntimes,nrows,ncols,minpsl,maxpsl,GridSize,timeinterval,HDFgroup,outfilefolder)



