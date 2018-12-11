import open3d
import argparse
import RealSenseRecorder
import Reconstructor
import atexit
import os
import sys
import json
import pyrealsense2 as rs2
from Logger import Logger



def main() :

    os.system("cls")

    rootDir = os.path.join(os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop"), "Workspace")

    parser = argparse.ArgumentParser(description="Virtual Vision v0.0")
    modeGroup = parser.add_mutually_exclusive_group(required=True)
    scanGroup = modeGroup.add_argument_group(title="Scanning options")
    scanParamGroup = scanGroup.add_mutually_exclusive_group()
    scanConfigGroup = scanGroup.add_mutually_exclusive_group()
    reconstructGroup = modeGroup.add_argument_group(title="Reconstructing options")


    modeGroup.add_argument("--scan", action="store", nargs=1, default=False, type=int, required=False, help="Record a new scan of the environment : 0/1")
    scanGroup.add_argument("--nsec", action="store", nargs=1, default=[0], type=int, required=False, help="Set the scan duration in seconds (0 for unlimited, press Q to quit)")
    scanGroup.add_argument("--workspace", action="store", nargs=1, default=rootDir, type=str, required=False, help="Workspace directory, Desktop/Workspace by default")
    scanGroup.add_argument("--sharpening", action="store", nargs=1, default=[0], type=int, required=False, help="Sharpen blurry images : 0/1")

    scanConfigGroup.add_argument("--sconfig", action="store", nargs=1, type=str, required=False, help="Import a JSON RealSense configuration file (instead of parameters) : path")
    scanParamGroup.add_argument("--fps", action="store", nargs=1, default=[30], type=int, required=False, help="Set the RealSense framerate, default : 30")
    scanParamGroup.add_argument("--width", action="store", nargs=1, default=[1280], type=int, required=False, help="Set the RealSense width, default : 1280")
    scanParamGroup.add_argument("--height", action="store", nargs=1, default=[720], type=int, required=False, help="Set the RealSense height, default : 720")
    scanParamGroup.add_argument("--vpreset", action="store", nargs=1, default=[3], type=int, required=False, help="Set the RealSense visual preset (0 -> Custom, 1 -> Default, 2 -> Hand, 3 -> High Accuracy, 4 -> High Density, 5 -> Medium Density), default : 3")
    scanParamGroup.add_argument("--laserpower", action="store", nargs=1, default=[240], type=int, required=False, help="Set the RealSense laser power, default : 240")
    scanParamGroup.add_argument("--exposure", action="store", nargs=1, default=[3200], type=int, required=False, help="Set the RealSense exposure, default : 3200")
    scanParamGroup.add_argument("--gain", action="store", nargs=1, default=[16], type=int, required=False, help="Set the RealSense gain, default : 16")

    modeGroup.add_argument("--reconstruct", action="store", nargs=1, default=False, type=int, required=False, help="Reconstruct a dataset : 0/1")
    reconstructGroup.add_argument("--rconfig", action="store", nargs=1, default="", type=str, required=("--reconstruct" in sys.argv), help="Import a JSON parameter file : path")

    args = parser.parse_args()

    if args.scan :

        args.scan = True

        parameters = {
            "Scanning Mode" : True,
            "Reconstructing Mode" : False,
            "Scan Duration (s)" : args.nsec[0],
            "Workspace Root" : '"' + args.workspace + '"',
            "Sharpening RGB Frames" : bool(args.sharpening[0]),
            "RS Configuration File" : '"' + args.sconfig[0] + '"' if args.sconfig else '""'
            }

    elif args.reconstruct :

        args.reconstruct = True

        parameters = {
            "Scanning Mode" : False,
            "Reconstructing Mode" : True,
            "Reconstruction Parameter File" : '"' + args.rconfig[0] + '"'
            }

    else :

        Logger.printError("Please set --scan or --reconstruct to 1")
        exit()

    Logger.printParameters("PARAMETERS", parameters)

    if parameters["Scanning Mode"] :

        if args.sconfig :

            Logger.printInfo("Loading parameters from file : " + parameters["RS Configuration File"])

            rsr = RealSenseRecorder.RealSenseRecorder(
                scanDuration=parameters["Scan Duration (s)"],
                fps=None,
                width=None,
                height=None,
                visualPreset=None,
                laserPower=None,
                exposure=None,
                gain=None,
                rootDir=parameters["Workspace Root"].replace('"', ""),
                sharpening=parameters["Sharpening RGB Frames"],
                configFile=parameters["RS Configuration File"].replace('"', "")
            )

        else :

            cameraParameters = {
                "FPS" : args.fps[0],
                "Width" : args.width[0],
                "Height" : args.height[0],
                "Visual Preset" :  args.vpreset[0],
                "Laser Power" :  args.laserpower[0],
                "Exposure" :  args.exposure[0],
                "Gain" :  args.gain[0]
                }
            Logger.printParameters("CAMERA PARAMETERS", cameraParameters)

            rsr = RealSenseRecorder.RealSenseRecorder(
                scanDuration=parameters["Scan Duration (s)"],
                fps=cameraParameters["FPS"],
                width=cameraParameters["Width"],
                height=cameraParameters["Height"],
                visualPreset=cameraParameters["Visual Preset"],
                laserPower=cameraParameters["Laser Power"],
                exposure=cameraParameters["Exposure"],
                gain=cameraParameters["Gain"],
                rootDir=parameters["Workspace Root"].replace('"', ""),
                sharpening=parameters["Sharpening RGB Frames"],
                configFile=None
            )

        Logger.printOperationTitle("SCANNING")

        rsr.setupFolder()
        rsr.scan()

        atexit.register(rsr.close)

    elif parameters["Reconstructing Mode"] :

        reconstructor = Reconstructor.Reconstructor(parameters["Reconstruction Parameter File"])

        Logger.printOperationTitle("RECONSTRUCTING")

if __name__ == "__main__" :
    main()
