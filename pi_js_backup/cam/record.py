import cv2
import time
from datetime import datetime
import argparse

log_file = '/home/ad01/bee/cam/record.log'

def record_video(duration, output_file):
    # Open default camera
    cap = cv2.VideoCapture(0)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    out = cv2.VideoWriter(output_file, fourcc, 30.0, (640, 480))

    start_time = time.time()
    while int(time.time() - start_time) < duration:
        ret, frame = cap.read()
        if ret:
            # Write the frame into the file
            out.write(frame)
            #cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break

    # Release everything if job is finished
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Record video from webcam.')
    parser.add_argument('--name', type=str, help='Output filename (including .mp4 extension)')
    args = parser.parse_args()

    if args.name:
        output_filename = "/home/ad01/bee/record/"+args.name
    else:
        current_datetime = datetime.now()
        output_filename = current_datetime.strftime("/home/ad01/bee/record/%Y-%m-%d_%H-%M-%S") + '.mp4'

    with open(log_file, 'a') as f:
        # Write start of execution to log
        f.write(f'Starting execution at {datetime.now()}\n')

        duration = 60  # 1 minute
        record_video(duration, output_filename)

        # Write end of execution to log
        f.write(f'Execution completed at {datetime.now()}\n')
