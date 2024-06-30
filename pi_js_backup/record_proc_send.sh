#!/bin/bash

# Define timestamp
timestamp=$(date +'%Y-%m-%d_%H-%M-%S')

# Execute record.py script with specified name
python /home/ad01/bee/cam/record.py --name "pi01_${timestamp}.mp4"
source /home/ad01/bee/bee/bin/activate
# Change directory to yolov5
cd /home/ad01/bee/yolov5

# Execute detect2_csv.py script with specified parameters
python detect2_csv.py --weight /home/ad01/bee/yolov5/bee/weight/best.pt --hide-labels --hide-conf --source /home/ad01/bee/record/"pi01_${timestamp}.mp4"

# Execute send.py script with specified parameters
python send.py --input /home/ad01/bee/record/"pi01_${timestamp}.mp4" \
                --output /home/ad01/bee/yolov5/result/"pi01_${timestamp}"/"pi01_${timestamp}.mp4" \
                --info /home/ad01/bee/yolov5/result/"pi01_${timestamp}"/additional_info.csv
deactivate

