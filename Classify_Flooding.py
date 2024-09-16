#!/usr/bin/env python

import sys
import numpy
import time
from osgeo import gdal, gdal_array
from osgeo.gdalconst import *
import psutil
import gc

def writeGDALRast(rast, nrows, ncols, xll, yll, csize, ndata, projection, outfile):
       #start gdal Exceptions
       gdal.UseExceptions()
       #open gdal raster
       src_ds=gdal_array.OpenArray(rast)
       dst_ds=gdal.GetDriverByName(str('GTiff')).CreateCopy(str(outfile),src_ds,0,["COMPRESS=LZW", "BIGTIFF=YES"])
       geotrans=(numpy.float64(xll),numpy.float64(csize),0,numpy.float64(yll)+numpy.float64(csize)*int(nrows),0,numpy.float64(csize)*(-1))
       dst_ds.SetProjection(projection)
       dst_ds.SetGeoTransform(geotrans)
       dst_ds.GetRasterBand(1).SetNoDataValue(float(ndata))
       dst_ds=None
       src_ds=None
       return


def readGDALRast(infile):
        #open gdal file
        #print("Opening gdal source...")
        indata=gdal.Open(infile, GA_ReadOnly)
        #get geo transformation data:
        geotrans=indata.GetGeoTransform()
        projection=indata.GetProjectionRef()
        x= geotrans[0]
        y= geotrans[3]
        xres = geotrans[1]
        yres = geotrans[5]
        nrows = indata.RasterYSize
        ncols = indata.RasterXSize
        nbands = indata.RasterCount
        #print("\t\tX-Origin: "+str(x))
        #print("\t\tY-Origin: "+str(y))
        #print("\t\tPixel Width: "+str(xres))
        #print("\t\tPixel Height: "+str(yres))
        print("\t\tnrows: "+str(nrows))
        print("\t\tncols: "+str(ncols))
        #print (float(xres) < 0,float(yres) < 0)
        llx=x
        #yres is negative
        lly=y+nrows*yres
        #print("\t\tNrows: "+str(nrows))
        #print("\t\tNcols: "+str(ncols))
        #print("\t\tNumber of bands: "+str(nbands))
        #print("\t\tCreating output file...")
        band=indata.GetRasterBand(1)
        outdat=band.ReadAsArray()
        try:
            noDATA=indata.GetNoDataValue()
        except:
            noDATA=indata.GetRasterBand(1).GetNoDataValue()
        #print("\t\tNoDATA: "+str(noDATA))
        return (outdat,nrows,ncols,llx,lly,xres,noDATA,projection)

def classify(floodmap,nrows,ncols,xll, yll, xres, noDATA, projection):

    floodmap_class = numpy.full((nrows,ncols),-9999)
    print("Flood map", floodmap.shape)
    #Rules applied:
    
    floodmap_class = numpy.where( (floodmap > 0) & (floodmap < 0.1),1,floodmap_class)
    floodmap_class = numpy.where( (floodmap >= 0.1) & (floodmap < 1),2,floodmap_class)
    floodmap_class = numpy.where( (floodmap >= 1) & (floodmap < 2.5),3,floodmap_class)
    floodmap_class = numpy.where( (floodmap >= 2.5) ,4,floodmap_class)
    
    del(floodmap)
    x = gc.collect()
    print('RAM memory % used:', psutil.virtual_memory()[2])
    print("Computed Flood map classified")
    return floodmap_class
    
if __name__=="__main__": 

    start = time.time()
    # Getting % usage of virtual_memory ( 3rd field)
    print('RAM memory % used:', psutil.virtual_memory()[2])
    
    indir=sys.argv[1]
    rp=sys.argv[2]
    outdir=indir
    
    #Layers to define imperviousness
    print("Reading Map")
    infile=indir + "/FinalDepth"+rp+"y.tif"
    floodmap,nrows,ncols,xll,yll,xres,noDATA,projection=readGDALRast(infile)

    print('RAM memory % used:', psutil.virtual_memory()[2])
    
    print(ncols,nrows)
    floodmap_class=classify(floodmap,nrows,ncols,xll, yll, xres, noDATA, projection)

    outfile=outdir+"/FinalDepth"+rp+"y_Class.tif"
    writeGDALRast(floodmap_class, nrows, ncols, xll, yll, xres, noDATA, projection, outfile)
    
    print("Runtime is " + str(time.time() - start))
