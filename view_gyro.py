import sys
import subprocess
import logging
import argparse

import compute_data
import model_to_js

def extract_info_from_video_file(video_file_name):
    cmd = subprocess.run("wsl wslpath -a -u {}".format(video_file_name), capture_output=True, text=True, check=True) 
    wsl_video_file_name = cmd.stdout.split('\n')[0]

    exif_cmd = "wsl -e /home/olive/workspace/exiftool/Image-ExifTool-12.73/exiftool -m -api largefilesupport=1 -g3 -j -ee -TimeCode -Accelerometer -AngularVelocity {}".format(wsl_video_file_name)

    logging.info("execute command: " + exif_cmd)

    try:
        result = subprocess.run(exif_cmd, capture_output=True, text=True)
    except:
        logging.error("exif treatment fails")

    txt_file_name = video_file_name.split('.')[0] + ".json"
    with open(txt_file_name, "w+") as f:
        f.write(result.stdout)
    
    return txt_file_name


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str)
    parser.add_argument("-q", "--query", type=str)
    parser.add_argument("-c", "--calibration", action='store_true')
    parser.add_argument("-f", "--force", action='store_true')
    args = parser.parse_args()

    query = args.query
    calibration = args.calibration
    force = args.force

    if len(sys.argv) > 1:
        video_file_name = sys.argv[1]
    else:
        logging.error("Missing video file name")

    video_file_name = args.input
    if video_file_name[-4:] == 'insv':
        logging.info("Processing video file " + video_file_name)
        json_file = extract_info_from_video_file(video_file_name)
        logging.info("json file generated: " + json_file)
    elif video_file_name[-4:] == 'json':
        json_file = video_file_name

    logging.info("Process data")
    compute_data.compute(json_file, query, calibration, force)
    logging.info("End of data processing")
    
    logging.info("Generating 3D model")
    model_dir = "3D_models"
    model_to_js.process_models(model_dir)

    logging.info("End of process")
