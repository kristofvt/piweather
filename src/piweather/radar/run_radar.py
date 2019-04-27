import h5py
import numpy as np
#from matplotlib import pyplot as plt
#import pyproj
#import shapely.geometry
from ftplib import FTP
import os, glob
import datetime
import urllib
from dateutil import tz
import subprocess
import rasterio

def download_data_forecast(dir):
    # Get current time and convert to proper format
    currentTime = datetime.datetime.now()
    currentYear = currentTime.strftime('%Y')
    currentMonth = currentTime.strftime('%m')
    currentDay = currentTime.strftime('%d')

    # Convert time to UTC timezone
    startTime = currentTime.strftime('%H%M')
    from_zone = tz.tzlocal()
    to_zone = tz.tzutc()

    utc = datetime.datetime(int(currentYear), int(currentMonth), int(currentDay), int(startTime[0:2]),
                            int(startTime[2:4]))
    utc = utc.replace(tzinfo=from_zone)

    # Convert time zone
    utcTime = utc.astimezone(to_zone)

    print('Retrieved UTC time: {}'.format(utcTime))

    currentYear = utcTime.strftime('%Y')
    currentMonth = utcTime.strftime('%m')
    currentDay = utcTime.strftime('%d')

    # FTP connection
    print('Connecting to data.knmi.nl')
    ftp = FTP('data.knmi.nl')
    ftp.login()
    print('Downloading radar data ...')
    ftp.cwd('download/radar_forecast/1.0/noversion/' + currentYear + '/' + currentMonth + '/' + currentDay)
    files = sorted(ftp.nlst())

    # Get the latest radar file
    file = files[-1]

    print('Downloading remote file: {}'.format(file))

    # Download the file
    oldFiles = glob.glob(os.path.join(dir, '*h5'))
    for f in oldFiles: os.remove(f)
    with open(os.path.join(dir, file), 'wb') as f:
        ftp.retrbinary("RETR " + file, f.write)

    print('Radar data downloaded')

    return os.path.join(dir, file)

def download_data_pasthour(dir):

    # Clean up directory
    oldFiles = glob.glob(os.path.join(dir, '*NA*.h5'))
    for f in oldFiles: os.remove(f)

    # Get current time and convert to proper format
    currentTime = datetime.datetime.now()
    currentYear = currentTime.strftime('%Y')
    currentMonth = currentTime.strftime('%m')
    currentDay = currentTime.strftime('%d')

    # Convert time to UTC timezone
    startTime = currentTime.strftime('%H%M')
    from_zone = tz.tzlocal()
    to_zone = tz.tzutc()

    utc = datetime.datetime(int(currentYear), int(currentMonth), int(currentDay), int(startTime[0:2]),
                            int(startTime[2:4]))
    utc = utc.replace(tzinfo=from_zone)

    # Convert time zone
    utcTime = utc.astimezone(to_zone)

    print('Retrieved UTC time: {}'.format(utcTime))

    currentYear = utcTime.strftime('%Y')
    currentMonth = utcTime.strftime('%m')
    currentDay = utcTime.strftime('%d')

    # FTP connection
    print('Connecting to data.knmi.nl')
    ftp = FTP('data.knmi.nl')
    ftp.login()
    print('Downloading radar data ...')
    ftp.cwd('/download/radar_reflectivity_composites/2.0/noversion/' + currentYear + '/' + currentMonth + '/' + currentDay)
    files = sorted(ftp.nlst())

    # Get the most recent file
    newestFile = files[-1]

    # Get the time of the most recent file
    newestFileTime = datetime.datetime(int(currentYear), int(currentMonth), int(currentDay),
                                       int(newestFile.split('_')[4][0:2]),  int(newestFile.split('_')[4][2:4]))

    # Construct a datelist for the past hour
    date_list = list(reversed([newestFileTime - datetime.timedelta(minutes=x) for x in range(0, 65, 5)]))

    # We need to save the time of the first file, this will be the basetime for calculating the timeline
    # and we need it in the local time zone!
    baseTimeLocal = date_list[0].replace(tzinfo=to_zone).astimezone(from_zone)

    # Back to root dir
    ftp.cwd('/download/radar_reflectivity_composites/2.0/noversion/')

    # Download the appropriate files
    files = []
    for date in date_list:
        year = date.strftime('%Y')
        month = date.strftime('%m')
        day = date.strftime('%d')
        hour = date.strftime('%H')
        minutes = date.strftime('%M')
        remoteFile = year + '/' + month + '/' + day + '/' + 'RAD_NL25_PCP_NA_' + hour + minutes + '.h5'

        print('Downloading remote file: {}'.format(remoteFile))
        with open(os.path.join(dir, os.path.basename(remoteFile)), 'wb') as f:
            ftp.retrbinary("RETR " + remoteFile, f.write)

        files.append(os.path.basename(remoteFile))

    print('Radar data downloaded')

    return files, baseTimeLocal

def read_radar_data(dir, pasthour_files, forecast_file):

    print('Reading data from hdf5 file ...')

    # Past hour data
    data = np.zeros((765, 700, 19), dtype=np.uint8)
    for t in range(13):
        # Open the radar file
        f = h5py.File(os.path.join(dir, pasthour_files[t]), 'r+')
        data[:, :, t] = np.array(f['image1']['image_data'])

    # Forecast data
    # Open the radar file
    f = h5py.File(forecast_file, 'r+')
    for t in range(6):
        data[:, :, t+13] = np.array(f['image' + str(t+3)]['image_data']) # First image discarded

    print('Rescaling data ...')
    data[data == 255] = 0
    data = 0.5 * data - 32
    data[data < 5] = 0
    data = data.astype(np.uint8)

    print('Perform pretty simple noise filtering ...')
    sumValid = np.sum(data != 0, axis=2)
    idxNoise = np.where(sumValid == 1) # Only once in the time series, there is a signal -> likely noise
    data[idxNoise[0], idxNoise[1], :] = 0

    return data

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

    if os.path.exists(file): os.remove(file)

    with rasterio.open(file, 'w', driver='GTiff',
                       height=data.shape[0], width=data.shape[1],
                       count=data.shape[2], dtype=rasterio.uint8,
                       crs=crs.astype(str), transform=transform, nodata=0) as dst:
        for band in range(data.shape[2]):
            dst.write(data[:, :, band], band + 1)

def reproject(infile, outfile):

    if os.path.exists(outfile): os.remove(outfile)

    print('Reprojecting to EPSG:3857 ...')
    subprocess.call(
        'gdalwarp -t_srs EPSG:3857 -tr 750 750 -r BILINEAR {} {}'.format(infile,outfile), shell=True)


def toPNG(infile, outPattern, base_time, colorRamp):

    print('Removing old file ...')
    images = glob.glob(os.path.join(os.path.dirname(infile), 'radar*.png'))
    for f in images: os.remove(f)

    print('Converting to PNGs ...')
    with rasterio.open(infile) as src: bands = src.count
    for band in range(bands):
        print('Image: {}/{}'.format(band + 1, bands))
        currentTime = (base_time + datetime.timedelta(minutes=5 * band)).strftime('%y%m%d%H%M')
        subprocess.call('gdaldem color-relief -of png -b {} -alpha {} {} {}'.format(str(band + 1),
                                                                                    infile,
                                                                                    colorRamp,
                                                                                    os.path.join(os.path.dirname(infile), outPattern + currentTime + '.png')),
                        shell=True)

    aux_files = glob.glob(os.path.join(os.path.dirname(infile), 'radar*.xml'))
    for f in aux_files: os.remove(f)


def upload_images(images):

    print('Connecting to weerturnhout.be over FTP ...')
    from ftplib import FTP
    ftps = FTP('web0110.zxcs.be')
    ftps.login('u44514p39920', 'xuQKHsXc')

    print('Check if folder needs to be cleaned ...')
    ftps.cwd('/domains/weerturnhout.be/public_html/radar/')
    contents = ftps.nlst()
    contents = list(sorted(contents))
    if len(contents) > 500:
        print('Cleaning archive ...')
        for f in contents[0:15]:
            if (f.startswith('radardataEPSG4326')) & (f.endswith('.png')):
                ftps.delete(f)
                print('Deleted: {}'.format(f))

    print('Uploading new files ...')
    for image in images:
        try:
            ftps.delete(os.path.basename(image))
        except: pass
        print(image)
        f = open(image, 'rb')
        ftps.storbinary('STOR {}'.format(os.path.basename(image)), f)
        f.close()
    print('All files uploaded to server ...')
    ftps.quit()

def renew_radar(radar_dir, last_processed):

    outTif = os.path.join(radar_dir, 'radar_data.tif')

    # Download forecast radar data
    forecast_file = download_data_forecast(radar_dir)

    # Download past hour radar data
    radar_files, localTime = download_data_pasthour(radar_dir)

    # Write the processed file to text file soon enough so new instance of script does not run
    if os.path.exists(last_processed): os.remove(last_processed)
    with open(last_processed, 'w') as file: file.write(radar_files[-1])

    # Extract the data
    radar_data = read_radar_data(radar_dir, radar_files, forecast_file)

    # Get projection
    transform, crs = get_projection_transform(os.path.join(radar_dir, radar_files[0]))

    # Write 2 tif
    write2tif(radar_data, outTif, transform, crs)

    # Reproject to EPSG3857
    projectedTif = os.path.splitext(outTif)[0] + '_EPSG3857.tif'
    reproject(outTif, projectedTif)

    # Export to PNGs
    colorRamp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'radarcolors.txt')
    toPNG(projectedTif, 'radardataEPSG3857_', localTime, colorRamp)

    # Upload to server
    images = glob.glob(os.path.join(radar_dir, 'radar*.png'))
    upload_images(images)

def check_new_imagery(old_file):

    # Get current time and convert to proper format
    currentTime = datetime.datetime.now()
    currentYear = currentTime.strftime('%Y')
    currentMonth = currentTime.strftime('%m')
    currentDay = currentTime.strftime('%d')

    # Convert time to UTC timezone
    startTime = currentTime.strftime('%H%M')
    from_zone = tz.tzlocal()
    to_zone = tz.tzutc()

    utc = datetime.datetime(int(currentYear), int(currentMonth), int(currentDay), int(startTime[0:2]),
                            int(startTime[2:4]))
    utc = utc.replace(tzinfo=from_zone)

    # Convert time zone
    utcTime = utc.astimezone(to_zone)

    print('Retrieved UTC time: {}'.format(utcTime))

    currentYear = utcTime.strftime('%Y')
    currentMonth = utcTime.strftime('%m')
    currentDay = utcTime.strftime('%d')

    # FTP connection
    print('Connecting to data.knmi.nl')
    ftp = FTP('data.knmi.nl')
    ftp.login()
    print('Checking newest file ...')
    ftp.cwd(
        '/download/radar_reflectivity_composites/2.0/noversion/' + currentYear + '/' + currentMonth + '/' + currentDay)
    files = sorted(ftp.nlst())

    # Get the most recent file
    analysis_file = files[-1]

    # Check if we have processed this file already
    if analysis_file == old_file: return False
    else:
        # There's a new file, but first check if forecast file is ALSO available
        ftp.cwd('/download/radar_forecast/1.0/noversion/' + currentYear + '/' + currentMonth + '/' + currentDay)
        files = sorted(ftp.nlst())

        # Get the latest radar file
        forecast_file = files[-1]

        # Check if forecast file is from same time
        if os.path.splitext(analysis_file)[0][-4:] == os.path.splitext(forecast_file)[0][-4:]:
            return True
        else:
            print('forecast file is not in sync with analysis file!')
            return False

def main():

    radar_dir = '/home/pi/radar'
    last_processed = os.path.join(radar_dir, 'last_processed.txt')
    if not os.path.exists(last_processed): open(last_processed, 'w+').close()

    # Get last processed file
    with open(last_processed, 'r') as file: old_file = file.read()

    # Check if new imagery is available
    run_required = check_new_imagery(old_file)

    # If new imagery available, run processing chain
    if run_required:
        print('New imagery found -> processing chain starts ...')
        renew_radar(radar_dir, last_processed)
    else:
        print('No new imagery found -> exiting')

def plotColorbar():
    print('Creating color palette')

    ##### Create the color palette
    def interpolColors(color1, color2):
        R = np.linspace(color1[0], color2[0], 100)
        G = np.linspace(color1[1], color2[1], 100)
        B = np.linspace(color1[2], color2[2], 100)
        return R, G, B

    start_light = [193, 212, 242]
    start_dark = [135, 159, 198]
    startInterpol = interpolColors(start_light, start_dark)

    blue_light = [93, 162, 240]
    blue_dark = [31, 96, 171]
    blueInterpol = interpolColors(blue_light, blue_dark)

    green_light = [46, 255, 46]
    green_dark = [1, 81, 12]
    greenInterpol = interpolColors(green_light, green_dark)

    yellow_light = [255, 247, 0]
    yellow_dark = [255, 131, 0]
    yellowInterpol = interpolColors(yellow_light, yellow_dark)

    red_light = [255, 0, 0]
    red_dark = [104, 3, 3]
    redInterpol = interpolColors(red_light, red_dark)

    purple_light = [243, 14, 243]
    purple_dark = [97, 3, 104]
    purpleInterpol = interpolColors(purple_light, purple_dark)

    grey_light = [255, 255, 255]
    grey_dark = [156, 156, 156]
    greyInterpol = interpolColors(grey_light, grey_dark)

    finalColors = np.empty((0, 3))
    finalColors = np.concatenate((finalColors, np.array(startInterpol).transpose()), axis=0)
    finalColors = np.concatenate((finalColors, np.array(blueInterpol).transpose()), axis=0)
    finalColors = np.concatenate((finalColors, np.array(greenInterpol).transpose()), axis=0)
    finalColors = np.concatenate((finalColors, np.array(yellowInterpol).transpose()), axis=0)
    finalColors = np.concatenate((finalColors, np.array(redInterpol).transpose()), axis=0)
    finalColors = np.concatenate((finalColors, np.array(purpleInterpol).transpose()), axis=0)
    finalColors = np.concatenate((finalColors, np.array(greyInterpol).transpose()), axis=0)
    finalColors = finalColors / 255.

    from matplotlib import pyplot as plt
    import matplotlib as mpl
    fig = plt.figure(figsize=(25, 20))
    fig.patch.set_facecolor([0.5, 0.5, 0.5])
    ax = plt.gca()
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.spines['left'].set_color('white')

    customColors = mpl.colors.ListedColormap(finalColors)
    plt.pcolor(np.zeros((10, 10)), vmin=10, vmax=80, cmap=customColors)

    cb = plt.colorbar(aspect=40)
    cbytick_obj = plt.getp(cb.ax.axes, 'yticklabels')
    plt.setp(cbytick_obj, color='white', fontsize=24)
    cb.set_ticks([10, 20, 30, 40, 50, 60, 70, 77], update_ticks=True)
    tick_labels = ['0.1', '1', '5', '10', '20', '50', '100', 'Hagel']
    cb.set_ticklabels(tick_labels, update_ticks=True)
    cb.set_label('Neerslag intensiteit (mm/h)', color='white', fontsize=24, labelpad=10)

if __name__=="__main__":
   main()


#### LOOKUPTABLE FOR RADAR VALUES AND RAINFALL RATES

# RADAR BREAKPOINTS: 10,23,34,39,44,50,55
# RAINFALL BREAKPOINTS: 0.1, 1, 5, 10, 20, 50, 100
