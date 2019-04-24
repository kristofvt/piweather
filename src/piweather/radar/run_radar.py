import h5py
import numpy as np
#from matplotlib import pyplot as plt
#import pyproj
#import shapely.geometry
from ftplib import FTP
import os
import datetime
import urllib
from dateutil import tz
#import pandas as pd
import subprocess
import rasterio

def download_data(dir):

    # Get current time and convert to proper format
    currentTime = datetime.datetime.now()
    currentYear = currentTime.strftime('%Y')
    currentMonth = currentTime.strftime('%m')
    currentDay = currentTime.strftime('%d')

    # FTP connection
    print('Connecting to data.knmi.nl')
    ftp = FTP('data.knmi.nl')
    ftp.login()
    print('Downloading radar data ...')
    ftp.cwd('download/radar_forecast/1.0/noversion/' + currentYear + '/' + currentMonth + '/' + currentDay)
    files = sorted(ftp.nlst())

    # Get the latest radar file
    file = files[-1]

    # Download the file
    if os.path.exists(os.path.join(dir, 'radar.h5')): os.remove(
        os.path.join(dir, 'radar.h5'))
    with open(os.path.join(dir, 'radar.h5'), 'wb') as f:
        ftp.retrbinary("RETR " + file, f.write)

    print('Radar data downloaded')

    return os.path.join(dir, 'radar.h5')

def read_radar_data(file):

    # Open the radar file
    f = h5py.File(file, 'r+')

    print('Reading data from hdf5 file ...')

    data = np.zeros((765, 700, 13), dtype=np.uint8)
    for t in range(13):
        data[:, :, t] = np.array(f['image' + str(t + 1)]['image_data'])

    print('Rescaling data ...')
    data[data == 255] = 0
    data = 0.5 * data - 32
    data[data < 0] = 0
    data = data.astype(np.uint8)

    return data

def get_base_time(file):

    # Get current time and convert to proper format
    currentTime = datetime.datetime.now()
    currentYear = currentTime.strftime('%Y')
    currentMonth = currentTime.strftime('%m')
    currentDay = currentTime.strftime('%d')

    # Open the radar file
    f = h5py.File(file, 'r+')

    print('Extracting base time information ...')

    # Read the starttime of the radar file
    productStart = str(f['overview'].attrs['product_datetime_start'])
    productStart_datetime = pd.to_datetime(productStart.split("'")[1])

    # Convert time to local timezone
    startTime = file.split('_')[-1][0:4]
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()

    utc = datetime.datetime(int(currentYear), int(currentMonth), int(currentDay), int(startTime[0:2]),
                            int(startTime[2:4]))
    utc = utc.replace(tzinfo=from_zone)

    # Convert time zone
    localTime = utc.astimezone(to_zone)

    print('Retrieved base time: {}'.format(localTime))

    return localTime

def get_projection_transform(file):

    # Open the radar file
    f = h5py.File(file, 'r+')

    print('Setting up projection ...')

    projStr = f.get('geographic').get('map_projection').attrs.get('projection_proj4_params')

    col_offset = f.get('geographic').attrs.get('geo_column_offset')[0]
    row_offset = f.get('geographic').attrs.get('geo_row_offset')[0]
    xscale = f.get('geographic').attrs.get('geo_pixel_size_x')[0]
    yscale = f.get('geographic').attrs.get('geo_pixel_size_y')[0]

    ydim = 765
    xdim = 700

    x = (np.arange(xdim) + col_offset + 0.5) * xscale
    y = (np.arange(ydim) + row_offset + 0.5) * yscale

    left = x[0]
    bottom = y[-1]
    right = x[-1]
    top = y[0]

    transform = rasterio.transform.from_bounds(left, bottom, right, top, xdim, ydim)

    return transform, projStr

def write2tif(data, file, transform, crs):

    print('Writing to TIF file ...')

    with rasterio.open(file, 'w', driver='GTiff',
                       height=data.shape[0], width=data.shape[1],
                       count=data.shape[2], dtype=data.dtype,
                       crs=crs.astype(str), transform=transform, nodata=0) as dst:
        for band in range(data.shape[2]):
            dst.write(data[:, :, band], band + 1)

def reproject(infile, outfile):

    print('Reprojecting to WGS84 ...')
    subprocess.call(
        'gdalwarp -t_srs EPSG:4326 -r BILINEAR {} {}'.format(infile,outfile), shell=True)

def toPNG(infile, outPattern, base_time, colorRamp):

    print('Converting to PNGs ...')
    with rasterio.open(infile) as src: bands = src.count
    for band in range(bands):
        print('Image: {}/{}'.format(band + 1, bands))
        currentTime = (base_time + datetime.timedelta(minutes=5 * band)).strftime('%y%m%d%H%M')
        subprocess.call('gdaldem color-relief -of png -b {} -alpha {} {} {}'.format(str(band + 1),
                                                                                    infile,
                                                                                    colorRamp,
                                                                                    os.path.dirname(infile) + outPattern + currentTime + '.png'),
                        shell=True)

def main():

    radar_dir = '/home/pi/radar'
    outTif = os.path.join(radar_dir, 'radar_data.tif')

    # Download radar data
    radar_file = download_data(radar_dir)

    # Extract the data
    radar_data = read_radar_data(radar_file)

    # Get base time
    localTime = get_base_time(radar_file)

    # Get projection
    transform, crs = get_projection_transform(radar_file)

    # Write 2 tif
    write2tif(radar_data, outTif, transform, crs)

    # Reproject to WGS84
    projectedTif = os.path.splitext(outTif)[0] + '_EPSG4326.tif'
    reproject(outTif, projectedTif)

    # Export to PNGs
    colorRamp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'radarcolors.txt')

    toPNG(projectedTif, 'radardataEPSG4326_', localTime, colorRamp)

if __name__=="__main__":
   main()













#
#
#
# for t in range(25):
#     print('Image: {}/25'.format(t+1))
#
#     currentTime = (localTime + datetime.timedelta(minutes=5*t)).strftime('%H:%M')
#
#     fig = plt.figure(figsize=(25,20))
#     fig.patch.set_facecolor('black')
#     ax = plt.gca()
#     ax.spines['bottom'].set_color('white')
#     ax.spines['top'].set_color('white')
#     ax.spines['right'].set_color('white')
#     ax.spines['left'].set_color('white')
#
#     m = Basemap(llcrnrlon=x_min+1.5, llcrnrlat=y_min+0.2, urcrnrlon=x_max-1.5, urcrnrlat=y_max-1,
#                 resolution='h', projection='tmerc', lon_0=3., lat_0=51.5)
#     m.drawcoastlines(linewidth=1, linestyle='solid', color='white')
#     m.drawcountries(linewidth=1, linestyle='solid', color='white', antialiased=1, ax=None, zorder=None)
#
#     data = np.array(f['image'+str(t+1)]['image_data'])
#     masked_data = np.ma.masked_where(data == 0, data)
#     masked_data = 0.5 * masked_data -32
#
#     # plt.imshow(images[t], cmap=cm)
#     # plt.pause(0.05)
#     # m.pcolor(xNew, yNew, masked_data, vmin=cRange[0], vmax=cRange[1], latlon=True)
#
#     customColors = mpl.colors.ListedColormap(finalColors)
#     m.pcolor(xNew, yNew, masked_data, vmin=10, vmax=80, cmap=customColors, latlon=True)
#     # plt.pcolor(masked_data, vmin=10, vmax=80, cmap=customColors)
#     cb = plt.colorbar(aspect=40)
#     cbytick_obj = plt.getp(cb.ax.axes, 'yticklabels')
#     plt.setp(cbytick_obj, color='white', fontsize=24)
#     cb.set_ticks(np.arange(10,81,10), update_ticks=True)
#     cb.set_label('Radar intensiteit (dBz)', color='white', fontsize=24, labelpad=20)
#
#     plt.title(currentTime, fontsize = 30, y=1.02, color='white')
#     plt.tight_layout()
#     plt.savefig(os.path.join(r'C:\Users\vtrichtk\Downloads\temp', str(t) + '.png'), bbox_inches='tight', facecolor=fig.get_facecolor())
#     plt.close()
#
# print('All images generated')
# print('Assembling to animated GIF')
#
#
# print('Connecting to ftp.weerturnhout.be')
# from ftplib import FTP
# ftps = FTP('ftp.weerturnhout.be')
# ftps.login('ftpweerturn', 'cpbmhl.nzuveaosx5jidfyJwg')
# file = open(r'C:\Users\vtrichtk\Downloads\temp\radar.gif', 'rb')
# print('Uploading GIF')
# ftps.storbinary('STOR /ftpweerturn/weerturnhout.be/wwwroot/radar.gif', file)     # send the file
# file.close()                                    # close file and FTP
# ftps.quit()
# print('GIF uploaded')
# print('All done!')
#
#
#
#
#
#
#
#
#
#
# # subprocess.call('gdal_translate -of png {} {}'.format(r'C:\Users\vtrichtk\Desktop\temp\testEPSG4326Colored.tif',
# #                                                       r'C:\Users\vtrichtk\Desktop\temp\testEPSG4326_3.png'
# #                                                       ), shell=True)
#
#







# print('Creating color palette')
# ##### Create the color palette
# def interpolColors(color1, color2):
#     R = np.linspace(color1[0], color2[0], 100)
#     G = np.linspace(color1[1], color2[1], 100)
#     B = np.linspace(color1[2], color2[2], 100)
#     return R, G, B
#
#
# start_light = [193, 212, 242]
# start_dark = [135, 159, 198]
# startInterpol = interpolColors(start_light, start_dark)
#
# blue_light = [93, 162, 240]
# blue_dark = [31, 96, 171]
# blueInterpol = interpolColors(blue_light, blue_dark)
#
# green_light = [46, 255, 46]
# green_dark = [1, 81, 12]
# greenInterpol = interpolColors(green_light, green_dark)
#
# yellow_light = [255, 247,0]
# yellow_dark = [255, 131, 0]
# yellowInterpol = interpolColors(yellow_light, yellow_dark)
#
# red_light = [255, 0, 0]
# red_dark = [104, 3, 3]
# redInterpol = interpolColors(red_light, red_dark)
#
# purple_light = [243, 14, 243]
# purple_dark = [97, 3, 104]
# purpleInterpol = interpolColors(purple_light, purple_dark)
#
# grey_light = [255, 255, 255]
# grey_dark = [156, 156, 156]
# greyInterpol = interpolColors(grey_light, grey_dark)
#
# finalColors = np.empty((0, 3))
# finalColors = np.concatenate((finalColors, np.array(startInterpol).transpose()), axis=0)
# finalColors = np.concatenate((finalColors, np.array(blueInterpol).transpose()), axis=0)
# finalColors = np.concatenate((finalColors, np.array(greenInterpol).transpose()), axis=0)
# finalColors = np.concatenate((finalColors, np.array(yellowInterpol).transpose()), axis=0)
# finalColors = np.concatenate((finalColors, np.array(redInterpol).transpose()), axis=0)
# finalColors = np.concatenate((finalColors, np.array(purpleInterpol).transpose()), axis=0)
# finalColors = np.concatenate((finalColors, np.array(greyInterpol).transpose()), axis=0)
# finalColors = finalColors/255.
#
# print('Color palette created')
