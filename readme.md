# 3D viewer from gyroscope

Access to page for demo
[https://01ive.github.io/insta_gyro_visualizer](https://01ive.github.io/insta_gyro_visualizer)

## Extract info from 360 camera

### Prerequisit
exiftool installed.

### STEP 1 - extract exif data from video file in json format

This step generates a *<video_file_name>.json* file using *exiftool* command line.

Used options:

* **-m** ignore Minor Errors
* **-g3** Organize output by tag group
* **-j** Json output format
* **-ee** Extract information from embedded documents
* **-api** largefilesupport

[exiftool options documentation](https://exiftool.org/exiftool_pod.html#Option-Details)

Exemple os exif tool usage

```bash
exiftool -m -api largefilesupport=1 -g3 -j -ee -TimeCode -Accelerometer -AngularVelocity VID_20240530_173115_003.insv | tee tests/VID_20240530_173115_003.json
```

### STEP 2 - convert exif data from json format to csv

Generates *<video_file_name>.csv* file from *<video_file_name>.json*.

### STEP 3 - process accelerometer and gyroscope data

Generates pickle intermediate file *<video_file_name>.pkl*

### STEP 4 - calculate Kalman filter data

### STEP 5 - generate json files for positions

3 json files are generated including position in quaternion format:

* *<video_file_name>_acc.json*
* *<video_file_name>_gyro.json*
* *<video_file_name>_kalman.json*
