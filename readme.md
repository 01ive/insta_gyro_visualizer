# 3D viewer from gyroscope

Access to page
[https://01ive.github.io/insta_gyro_visualizer](https://01ive.github.io/insta_gyro_visualizer)

## Extract info from 360 camera

Using *exiftool* command line with options

* **-m** ignore Minor Errors
* **-g3** Organize output by tag group
* **-j** Json output format
* **-ee** Extract information from embedded documents
* **-api** largefilesupport

[exiftool options documentation](https://exiftool.org/exiftool_pod.html#Option-Details)

Exemple

```bash
exiftool -m -api largefilesupport=1 -g3 -j -ee -TimeCode -Accelerometer -AngularVelocity VID_20240530_173115_003.insv | tee tests/VID_20240530_173115_003.json
```

## Convert text to csv data

Using Python code convert txt exiftool output to csv data

Exemple

```bash
python convert_to_csv.py VID_20240530_173115_003.txt
```

## Filter and view data

Using Python

```bash
python plot_data.py
```
