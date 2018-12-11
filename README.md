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
- [ ] Dataset pre-Processing
- [ ] Fragment generation
- [ ] Fragment linkage
- [ ] Model cleaning/post-Processing

### VR integration

- [ ] Importation in Unity
- [ ] Automatic alignment
- [ ] Integration of the VR headset

### Detection and integration of real dynamic objects

- [ ] Detection of real dynamic objects (humans, animals, vehicles, ...)
- [ ] 3D localization of the detected objects
- [ ] Integration of the objects within the virtual world

### Development of a controller

- [ ] Development of the hardware
- [ ] Interfacing the hardware with Unity
- [ ] Enhancing the ergonomy

## How to use ?

Currently, Virtual-Vision all
