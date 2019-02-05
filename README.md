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
+ [Darknet Yolo V3](https://github.com/pjreddie/darknet)

## Project steps

### Generation of the virtual world

- [x] Dataset acquisition using an Intel RealSense D435
- [x] Dataset importation
- [x] Dataset pre-Processing
- [x] Shard generation
- [x] Shard linkage
- [x] Model cleaning/post-Processing

### OpenStack cloud support

- [x] Creating a Client / Server interface
- [ ] Enhancing the deployment of the server application

### Detection and integration of real dynamic objects

- [x] Automatic alignment and calibration of the depth camera with the room's 3D model
- [x] Detection of real dynamic objects (humans, animals, vehicles, ...)
- [x] 3D localization of the detected objects
- [x] Integration of the objects within the virtual world

### VR integration

- [ ] Integration of the VR headset

### Development of a controller

- [ ] Development of the hardware
- [ ] Interfacing the hardware with Unity
- [ ] Enhancing the ergonomy

## How to use - Cloud

```
usage: Launcher.py [-h] --address ADDRESS --port PORT [--workspace WORKSPACE]

Virtual Vision v0.1 - Cloud

optional arguments:
  -h, --help            show this help message and exit
  --address ADDRESS     Server's IP address
  --port PORT           Server's port
  --workspace WORKSPACE
                        Path of the workspace, where the datasets will be
                        saved. Default : 'USER/Workspace'
```

## How to use - Client

```
usage: Virtual_Vision.py [-h]
                         {scan,reconstruct,cloud,calibration,detection} ...

Virtual Vision v0.1 - Client

optional arguments:
  -h, --help            show this help message and exit

Operating Mode:
  {scan,reconstruct,cloud,calibration,detection}
                        Scan, Reconstruct or Cloud
    scan                Scanning mode
    reconstruct         Reconstruction mode
    cloud               Cloud based interaction and processing
    calibration         Depth camera calibration for real time 3D integration.
                        The arguments can be directly set in config.json
    detection           Real time detection and 3D integration. The arguments
                        can be directly set in config.json
```

### Scan parameters

```
usage: Virtual_Vision.py scan [-h] [--nsec NSEC] [--workspace WORKSPACE]
                              [--sharpening SHARPENING]
                              [--autoreconstruct AUTORECONSTRUCT]
                              [--depthanalysis DEPTHANALYSIS]
                              [--sconfig SCONFIG] [--fps FPS] [--width WIDTH]
                              [--height HEIGHT] [--vpreset VPRESET]
                              [--laserpower LASERPOWER] [--exposure EXPOSURE]
                              [--gain GAIN]

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
  --autoreconstruct AUTORECONSTRUCT
                        Automatically reconstruct the dataset after the scan.
                        Default : 1
  --depthanalysis DEPTHANALYSIS
                        Process the dataset in order to estimate the coverage
                        of the depth frames. Default : 0

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

### Reconstruction parameters (Local processing)

```
usage: Virtual_Vision.py reconstruct [-h] --rconfig RCONFIG

optional arguments:
  -h, --help         show this help message and exit
  --rconfig RCONFIG  Import a JSON dataset reconstruction settings file : path
```

### Cloud parameters (Remote processing)

```
usage: Virtual_Vision.py cloud [-h] [--address ADDRESS] [--port PORT]
                               [--reconstruct RECONSTRUCT] [--list LIST]
                               [--remove REMOVE] [--getresult GETRESULT]
                               [--mergeshards MERGESHARDS]

optional arguments:
  -h, --help            show this help message and exit
  --address ADDRESS     Cloud server's IP address.
  --port PORT           Cloud server's port.
  --reconstruct RECONSTRUCT
                        Cloud based reconstruction, using the specified
                        reconstruction settings file : path
  --list LIST           Displays the name of the dataset present on the cloud.
  --remove REMOVE       Removes one dataset present on the cloud by specifying
                        its name
  --getresult GETRESULT
                        Downloads the point cloud of the specified
                        reconstructed dataset (name)
  --mergeshards MERGESHARDS
                        Merges the shards of the specified dataset (name).
                        Works only if the reconstruction ended before
                        successfully merging the shards
```

### Camera calibration parameters

```
usage: Virtual_Vision.py calibration [-h]

optional arguments:
  -h, --help  show this help message and exit
```
The variables can be directly tweaked using the ```config.json``` file.

### Real time detection and 3D integration parameters

```
usage: Virtual_Vision.py detection [-h]

optional arguments:
  -h, --help  show this help message and exit
```
The variables can be directly tweaked using the ```config.json``` file.

## Examples

Currently, Virtual-Vision allows to :

1. Record a dataset using an Intel RealSense and the following command :
```
python Virtual_Vision.py scan
```
2. Reconstruct a dataset by using a dataset JSON configuration file and the following command :
```
python Virtual_Vision.py reconstruct --rconfig PATH_OF_CONFIG_FILE
```
3. Launch the cloud server by using the following command :
```
python Launcher.py --address ADDRESS --port PORT
```
4. Interact with the cloud server by using the default config.json file (no argument speficied) or the server's address and port, in addition to a command (see below)
```
python Virtual_Vision.py cloud --address ADDRESS --port PORT --COMMAND
python Virtual_Vision.py cloud --COMMAND
```
5. Reconstruct a dataset on the cloud using the dataset JSON configuration file and the following command :
```
python Virtual_Vision.py cloud --reconstruct PATH_OF_CONFIG_FILE
```
6. List all the datasets on the cloud using the following command :
```
python Virtual_Vision.py cloud --list 1
```
7. Download the result (assembled point cloud) of a dataset by using the following command :
```
python Virtual_Vision.py cloud --getresult DATASET_NAME
```
8. Remove a dataset from the cloud's workspace by using the following command :
```
python Virtual_Vision.py cloud --remove DATASET_NAME
```
9. Merge the shards of one dataset (useful if the reconstruction process stopped before the shard assembling as it allows to skip the shard geenration process) by using the following command :
```
python Virtual_Vision.py cloud --mergeshards DATASET_NAME
```
10. Calibrate the camera by calculating the 3D transformation between the camera's point of and the "World" point cloud, by using the following command :
```
python Virtual_Vision.py calibrate
```
11. Launch the real time detection and 3D integration by using the following command :
```
python Virtual_Vision.py detection
```
