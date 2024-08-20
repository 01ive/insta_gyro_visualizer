import sys
import subprocess
import logging

import convert_to_csv
import compute_data

def extract_info_from_video_file(video_file_name):
    cmd = subprocess.run("wsl wslpath -a -u {}".format(video_file_name), capture_output=True, text=True, check=True) 
    wsl_video_file_name = cmd.stdout.split('\n')[0]

    exif_cmd = "wsl -e /home/olive/workspace/exiftool/Image-ExifTool-12.73/exiftool -m -TimeCode -Accelerometer -AngularVelocity -g -api largefilesupport -S -ee {}".format(wsl_video_file_name)

    logging.info("execute command: " + exif_cmd)

    try:
        result = subprocess.run(exif_cmd, capture_output=True, text=True)
    except:
        logging.error("exif treatment fails")

    txt_file_name = video_file_name.split('.')[0] + ".txt"
    with open(txt_file_name, "w+") as f:
        f.write(result.stdout)
    
    return txt_file_name


if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_file_name = sys.argv[1]
    else:
        logging.error("Missing video file name")
    
    logging.info("Processing video file " + video_file_name)
    
    txt_file = extract_info_from_video_file(video_file_name)
    logging.info("text file generated: " + txt_file)

    csv_file = convert_to_csv.convert_to_csv(txt_file)
    logging.info("csv file generated: " + csv_file)

    compute_data.compute_data(csv_file)
    logging.info("End of process")
