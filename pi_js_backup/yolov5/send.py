import argparse
import csv
import requests
import os

def extract_video_info(input_video):
    filename = os.path.basename(input_video)
    hive_name = filename.split('_')[0]
    hive = hive_name[2:]
    hive=int(hive)
    print(hive)
    name_video = filename.split('_')[1].split('.')[0] + " "+filename.split('_')[2].split('.')[0]
    return hive, name_video

def send_video(input_video, output_video, hive, name_video, max_count, min_count, avg, median):
    # Opening input and output video files
    with open(input_video, 'rb') as input_file, open(output_video, 'rb') as output_file:
        data = {"hive": hive, 'name_video': name_video, 'max': max_count, 'min': min_count, 'avg': avg, 'median': median}
        files = {'record': input_file, 'result': output_file}

        try:
            response = requests.post('http://mica.edu.vn:50208/api/video', files=files, data=data)
            if response.status_code == 200:
                print('Gửi thành công')
            else:
                print(f'Gửi không thành công, mã lỗi: {response.status_code}')
        except requests.exceptions.RequestException as e:
            print(f'Lỗi: {e}')
            return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send video and related data.')
    parser.add_argument('--input', help='Link to the input video file')
    parser.add_argument('--output', help='Link to the output video file')
    parser.add_argument('--info', help='Link to the information CSV file')

    args = parser.parse_args()
    
    if args.input and args.output and args.info:
        if os.path.exists(args.input) and os.path.exists(args.output) and os.path.exists(args.info):
            hive, name_video = extract_video_info(args.input)
            # Extracting information from the info file
            with open(args.info, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    max_count = int(row['Max Detected'])
                    min_count = int(row['Min Detected'])
                    avg = float(row['Avg Detected'])
                    avg = round(avg, 2) 
                    median = int(row['Median Detected'])
                    break  # Assuming there's only one row of data in the file

            print(hive, name_video, max_count, min_count, avg, median)
            send_video(args.input, args.output, hive, name_video, max_count, min_count, avg, median)
        else:
            print("One or more of the provided paths doesn't exist.")
    else:
        print("Please provide links to the input, output, and info files using --input, --output, and --info respectively.")
