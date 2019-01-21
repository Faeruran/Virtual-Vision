# Virtual-Vision

## About the project

Virtual Vision is a computer vision project whose goal is to improve the monitoring of complex and vast environments using multiple technologies such as deep learning, virtual reality and 3D scanning. This projects allows one to :

1. Scan and obtain a 3D model of the environment to monitor
2. Watch and move within the virtual world (the 3D model), using a virtual reality headset and a controller
3. Detect and integrate dynamic objects such as humans, animals or vehicles within the virtual world, at their real location

## Resources

This project is currently being developed using the following libraries and devices :

+ [Open3D](https://github.com/IntelVCL/Open3D)
```
@article{Zhou2018,
	author    = {Qian-Yi Zhou and Jaesik Park and Vladlen Koltun},
	title     = {{Open3D}: {A} Modern Library for {3D} Data Processing},
	journal   = {arXiv:1801.09847},
	year      = {2018},
}
```
+ [Intel® RealSense™ SDK 2.0](https://github.com/IntelRealSense/librealsense)
+ [Intel® RealSense™ D435 (depth camera)](https://realsense.intel.com/)

## Project steps

### Generation of the virtual world

- [x] Dataset acquisition using an Intel RealSense D435
- [x] Dataset importation
- [x] Dataset pre-Processing
- [x] Shard generation
- [x] Shard linkage
- [x] Model cleaning/post-Processing

### OpenStack cloud support

- [ ] Creating a Client / Server interface
- [ ] Enhancing the deployment of the server application

### Detection and integration of real dynamic objects

- [ ] Automatic alignment and calibration of the depth camera with the room's 3D model
- [ ] Detection of real dynamic objects (humans, animals, vehicles, ...)
- [ ] 3D localization of the detected objects
- [ ] Integration of the objects within the virtual world

### VR integration

- [ ] Integration of the VR headset

### Development of a controller

- [ ] Development of the hardware
- [ ] Interfacing the hardware with Unity
- [ ] Enhancing the ergonomy

## How to use

```
usage: Virtual_Vision.py [-h] {scan,reconstruct} ...

Virtual Vision v0.0

optional arguments:
  -h, --help          show this help message and exit

Operating Mode:
  {scan,reconstruct}  Scan or Reconstruct
    scan              Scanning mode
    reconstruct       Reconstruction mode
```

### Scan parameters

```
usage: Virtual_Vision.py scan [-h] [--nsec NSEC] [--workspace WORKSPACE]
                              [--sharpening SHARPENING] [--sconfig SCONFIG]
                              [--fps FPS] [--width WIDTH] [--height HEIGHT]
                              [--vpreset VPRESET] [--laserpower LASERPOWER]
                              [--exposure EXPOSURE] [--gain GAIN]

optional arguments:
  -h, --help            show this help message and exit
  --nsec NSEC           Scan duration in seconds (0 for unlimited, press Q to
                        quit). Default : 0
  --workspace WORKSPACE
                        Path of the workspace, where the dataset will be
                        saved. Default : 'USER/Desktop/Workspace'
  --sharpening SHARPENING
                        Allows to sharpen the images in order to reduce the
                        impact of the motion blur. Default : 0

Automatic Configuration (JSON importation):
  --sconfig SCONFIG     Import a JSON RealSense configuration file (instead of
                        Manual Settings, can be generated using the RealSense
                        SDK) : path

Manual Settings:
  --fps FPS             Framerate of the capture (higher can reduce motion
                        blur). Default : 60
  --width WIDTH         Width of the captured frames. Default : 848
  --height HEIGHT       Height of the captured frames. Default : 480
  --vpreset VPRESET     Allows to choose some preset settings provided by the
                        RealSense SDK (0 -> Custom, 1 -> Default, 2 -> Hand, 3
                        -> High Accuracy, 4 -> High Density, 5 -> Medium
                        Density). Default 0 (custom)
  --laserpower LASERPOWER
                        RealSense laser power. Default : 240
  --exposure EXPOSURE   Exposure time of the RealSense sensor. Default : 3200
  --gain GAIN           RealSense sensor gain. Default : 16
```

### Reconstruction parameters

```
usage: Virtual_Vision.py reconstruct [-h] --rconfig RCONFIG

optional arguments:
  -h, --help         show this help message and exit
  --rconfig RCONFIG  Import a JSON dataset parameter file : path
```

Currently, Virtual-Vision allows to :

1. Record a dataset using an Intel RealSense and the following command :
```
python Virtual_Vision.py scan
```
2. Reconstruct a dataset by using a dataset JSON configuration file and the following command :
```
python Virtual_Vision.py reconstruct --rconfig PATH_OF_CONFIG_FILE
```
