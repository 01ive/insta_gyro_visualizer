# 3D viewer from gyroscope

## Extract info from 360 camera

Using *exiftool* command line with options

* **-m** ignore Minor Errors
* **-g** Organize output by tag group
* **-S** Very short output format
* **-ee** Extract information from embedded documents
* **-api** largefilesupport

[exiftool options documentation](https://exiftool.org/exiftool_pod.html#Option-Details)

Exemple

```bash
exiftool -m -TimeCode -Accelerometer -AngularVelocity -g -api largefilesupport -S -ee VID_20240530_173115_003.insv | tee VID_20240530_173115_003.txt
```

## Convert text to csv data

Using Python code convert txt exiftool output to csv data

Exemple

```bash
python convert_to_csv.py
```

## Filter and view data

Using Python

```bash
python plot_data.py
```
