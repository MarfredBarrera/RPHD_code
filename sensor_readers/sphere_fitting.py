import numpy as np
import math
import pandas as pd

#	fit a sphere to X,Y, and Z data points
#	returns the radius and center points of
#	the best fit sphere
def sphereFit(spX,spY,spZ):
    #   Assemble the A matrix
    spX = np.array(spX)
    spY = np.array(spY)
    spZ = np.array(spZ)
    A = np.zeros((len(spX),4))
    A[:,0] = spX*2
    A[:,1] = spY*2
    A[:,2] = spZ*2
    A[:,3] = 1

    #   Assemble the f matrix
    f = np.zeros((len(spX),1))
    f[:,0] = (spX*spX) + (spY*spY) + (spZ*spZ)
    C, residules, rank, singval = np.linalg.lstsq(A,f,rcond=None)

    #   solve for the radius
    t = ((C[0]*C[0])+(C[1]*C[1])+(C[2]*C[2])+C[3])[0]
    radius = math.sqrt(t)

    return radius, C[0], C[1], C[2]


if __name__ == '__main__':
    """ Test functionality """
    from optparse import OptionParser
    import argparse
    import time
    import keyboard
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['NDI', 'OptiTrack'], default='OptiTrack',help='sphere regression analysis: NDI or OptiTrack')

    args = parser.parse_args()

    if args.mode == 'OptiTrack':
        print("OptiTrack mode selected")
        # Load data from the OptiTrack CSV file
        file_path = 'optitrack_data.csv'  # Replace with the actual path to your CSV file
        data = pd.read_csv(file_path, skiprows=7)  # Skip the first 6 rows of metadata

        # Extract relevant columns
        X = data.iloc[:, 5]
        Y = data.iloc[:, 6]
        Z = data.iloc[:, 7]
    elif args.mode == 'NDI':
        print("NDI mode selected")
        # Load data from the NDI CSV file
        file_path = 'pivotNDI.csv'
        data = pd.read_csv(file_path, skiprows=1)  # Skip the first 6 rows of metadata

        # Extract relevant columns
        X = data.iloc[:, 6]
        Y = data.iloc[:, 7]
        Z = data.iloc[:, 8]


    r, x0, y0, z0 = sphereFit(X,Y,Z)

    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x=np.cos(u)*np.sin(v)*r
    y=np.sin(u)*np.sin(v)*r
    z=np.cos(v)*r
    x = x + x0
    y = y + y0
    z = z + z0

    from matplotlib import rcParams
    rcParams['font.family'] = 'serif'
    #   3D plot of the
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D


    #   3D plot of Sphere
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_wireframe(x, y, z, color="r", linewidth=0.5, alpha=0.5)
    ax.scatter(X, Y, Z, zdir='z', s=2, c='b',rasterized=True)
    ax.set_aspect('equal')
    # ax.set_xlim3d(-35, 35)
    # ax.set_ylim3d(-35,35)
    # ax.set_zlim3d(-70,0)
    ax.set_xlabel('$x$ (mm)',fontsize=16)
    ax.set_ylabel('\n$y$ (mm)',fontsize=16)
    zlabel = ax.set_zlabel('\n$z$ (mm)',fontsize=16)
    plt.show()
    plt.savefig('SphereFitting.png', format='png', dpi=300, bbox_extra_artists=[zlabel], bbox_inches='tight')

    