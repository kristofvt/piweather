#!/bin/bash

USER=pi
export USER

cd /home/pi/upload_image/

file=$(ls -t /home/pi/ftp/files/FI9805W_C4D6554030A1/snap/*.jpg | head -1)

rm *.jpg
rm *.png

cp $file /home/pi/upload_image/webcam_image.jpg

DATE=$(date +"%Y%m%d%H%M")
cp webcam_image*.jpg archive 
mv archive/webcam_image*.jpg archive/$DATE.jpg

sleep 5

wget -O current_T.txt "http://www.weerturnhout.be/current_T.txt"
file_T="current_T.txt"
temperature=$(cat $file_T)

convert -pointsize 24 -fill white -draw "text 1,45 'www.weerturnhout.be' "  webcam_image.jpg  webcam_merksplas.png
convert -pointsize 24 -fill white -draw "text 1080,24 'Merksplas ("$temperature"°C)  ' "  webcam_merksplas.png  webcam_merksplas.png

ncftpput -u u44514p39920 -p xuQKHsXc web0110.zxcs.be /domains/weerturnhout.be/public_html/ /home/$USER/upload_image/webcam_merksplas.png
#ncftpput -u ftpweerturn -p cpbmhl.nzuveaosx5jidfyJwg ftp.weerturnhout.be /domains/weerturnhout.be/public_html/sites/default/files/ /home/$USER/upload_image/webcam_merksplas.png
