from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt
import numpy as np
import h5py
import os

#using HDF file produces 3d plots of water table or phreatic surface depth. The face colour corresponds to the phreatic depth.
# by default it is produced at the final timestep (ntimes) with views every 10 degreees
#++++++++++++++++++++++++++++++++++++++++
#THINGS TO CHANGE

# path to h5 file
h5File = "output_Wansbeck_at_Mitford_shegraph.h5"

# name of HDF file output group
HDFgroup = '2 ph_depth'

#outfile location
outfilefolder = '5-output-WaterTable-3dplots'

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

            # data[nrows:ncols:time] ie [j,i,:]
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


def ThreeDPlot(ntimes,nrows,ncols,GridSize,mindem,maxdem,dem,HDFgroup,outfilefolder):

    X = np.arange(0,(ncols-1)*GridSize,GridSize)
    #print X.shape
    #X = np.arange(1,ncols)
    #print X.shape
    Y = np.arange(0,(nrows-1)*GridSize,GridSize)
    X, Y = np.meshgrid(X, Y)


    # repeated to produce a plot for each direction (azi)
    print '3d plot'
    #starting direction
    azi=0
    while azi < 360:
        fig = plt.figure(figsize=[12.0, 5.0])

        ax = plt.subplot(1, 1, 1,projection='3d')
        plt.title('Water Table Depth (m below ground)')
        h5datapsl=getpsl(ntimes-1,nrows,ncols,HDFgroup)
        r1=h5datapsl/h5datapsl.max()

        # plot phreatic levels (m above ground)
        #r2=dem-h5datapsl
        #r3=r2/np.nanmax(r2)
        #surf = ax.plot_surface(Y, X, dem, rstride=1, cstride=1, facecolors=cm.Blues_r(r3), shade=False)

        surf = ax.plot_surface(Y, X, dem, rstride=1, cstride=1, facecolors=cm.Blues_r(r1), shade=False)
        ax.view_init(elev=20., azim=azi)
        ax.set_zlim(mindem,maxdem)
        ax.set_xlabel('Distance(m)')
        ax.set_ylabel('Distance(m)')
        ax.set_zlabel('Elevation(m)')

        #ax.yaxis.set_major_locator(LinearLocator(4))
        #ax.xaxis.set_major_locator(LinearLocator(4))

        #sets the scale bar. This is a bit of a fiddle
        h5datapsl[h5datapsl==-1.0]=np.nan
        min3dpsl=np.nanmin(h5datapsl)
        max3dpsl=np.nanmax(h5datapsl)
        scale = np.zeros (shape=(nrows-1,ncols-1))
        scale[scale==0.0]=min3dpsl
        scale[0,0]=max3dpsl
        #m = cm.ScalarMappable(cmap=cm.YlGnBu)
        m = cm.ScalarMappable(cmap=cm.Blues_r)
        m.set_array(scale)
        plt.colorbar(m)
    
        plt.savefig(outfilefolder+'/'+'WaterTable-3d-view'+str(azi)+'.png')
        plt.close()
        azi+=10
    return



#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# make folder for graphs and outputs
if not os.path.exists(outfilefolder):
    os.mkdir(outfilefolder)

fh5 = h5py.File(h5File,'r')
dem,nrows,ncols = getElevations()

#sets values outside mask to nan
dem[dem==-1]=np.nan
mindem=np.nanmin(dem)
maxdem=np.nanmax(dem)

GridSize=getGridSize()

# get times of output. ntimes is the final time
psltimes=getpsltimes(HDFgroup)
dimstime = psltimes.shape
ntimes = dimstime[0]

# 3D surface plots - by default produced at final time
# figures produced by default at ntimes (this can be changed)
ThreeDPlot(ntimes,nrows,ncols,GridSize,mindem,maxdem,dem,HDFgroup,outfilefolder)




