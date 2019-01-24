import open3d
import argparse
import atexit
import os
import sys
import json
import pyrealsense2 as rs2
import time
sys.path.append("./Utils/")
from Logger import Logger
sys.path.append("./Scan/")
import RealSenseRecorder
sys.path.append("./Reconstruction/")
import Reconstructor
import ShardAssembler
sys.path.append("./Socket/")
import Socket


def main() :

    os.system("clear")

    rootDir = os.path.join(os.path.join(os.path.join(os.environ["HOME"]), "Bureau"), "Workspace")

    parser = argparse.ArgumentParser(description="Virtual Vision v0.1")
    modes = parser.add_subparsers(title = "Operating Mode", dest="mode", help="Scan or Reconstruct")
    scanParser = modes.add_parser("scan", help="Scanning mode")
    scanLoadGroup = scanParser.add_argument_group(title="Automatic Configuration (JSON importation)")
    scanManualGroup = scanParser.add_argument_group(title="Manual Settings")
    reconstructParser = modes.add_parser("reconstruct", help="Reconstruction mode")
    reconstructCloudManualGroup = reconstructParser.add_argument_group(title="Cloud based reconstruction manual settings")
    reconstructCloudLoadGroup = reconstructParser.add_argument_group(title="Cloud based reconstruction automatic configuration (JSON importation)")

    scanParser.add_argument("--nsec", action="store", nargs=1, default=[0], type=int, required=False, help="Scan duration in seconds (0 for unlimited, press Q to quit). Default : 0")
    scanParser.add_argument("--workspace", action="store", nargs=1, default=rootDir, type=str, required=False, help="Path of the workspace, where the dataset will be saved. Default : 'USER/Desktop/Workspace'")
    scanParser.add_argument("--sharpening", action="store", nargs=1, default=[0], type=int, required=False, help="Allows to sharpen the images in order to reduce the impact of the motion blur. Default : 0")
    scanParser.add_argument("--autoreconstruct", action="store", nargs=1, default=[1], type=int, required=False, help="Automatically reconstruct the dataset after the scan. Default : 1")

    scanLoadGroup.add_argument("--sconfig", action="store", nargs=1, type=str, required=False, help="Import a JSON RealSense configuration file (instead of Manual Settings, can be generated using the RealSense SDK) : path")

    scanManualGroup.add_argument("--fps", action="store", nargs=1, default=[60], type=int, required=False, help="Framerate of the capture (higher can reduce motion blur). Default : 60")
    scanManualGroup.add_argument("--width", action="store", nargs=1, default=[848], type=int, required=False, help="Width of the captured frames. Default : 848")
    scanManualGroup.add_argument("--height", action="store", nargs=1, default=[480], type=int, required=False, help="Height of the captured frames. Default : 480")
    scanManualGroup.add_argument("--vpreset", action="store", nargs=1, default=[0], type=int, required=False, help="Allows to choose some preset settings provided by the RealSense SDK (0 -> Custom, 1 -> Default, 2 -> Hand, 3 -> High Accuracy, 4 -> High Density, 5 -> Medium Density). Default 0 (custom)")
    scanManualGroup.add_argument("--laserpower", action="store", nargs=1, default=[240], type=int, required=False, help="RealSense laser power. Default : 240")
    scanManualGroup.add_argument("--exposure", action="store", nargs=1, default=[3200], type=int, required=False, help="Exposure time of the RealSense sensor. Default : 3200")
    scanManualGroup.add_argument("--gain", action="store", nargs=1, default=[16], type=int, required=False, help="RealSense sensor gain. Default : 16")

    reconstructParser.add_argument("--rconfig", action="store", nargs=1, default="", type=str, required=True, help="Import a JSON dataset parameter file : path")
    reconstructParser.add_argument("--cloud", action="store", nargs=1, default=[1], type=int, required=False, help="Export the reconstruction process to a cloud infrastructure. Default : 1")

    reconstructCloudManualGroup.add_argument("--address", action="store", nargs=1, default="192.168.100.156", type=str, required=False, help="Reconstruction server's IP address.")
    reconstructCloudManualGroup.add_argument("--port", action="store", nargs=1, default="55555", type=str, required=False, help="Reconstruction server's port.")

    reconstructCloudLoadGroup.add_argument("--cconfig", action="store", nargs=1, default="", type=str, required=False, help="Import a JSON cloud settings file : path")

    args = parser.parse_args()

    if args.mode == "scan" :

        parameters = {
            "Scanning Mode" : True,
            "Reconstruction Mode" : bool(args.autoreconstruct[0]),
            "Scan Duration (s)" : args.nsec[0],
            "Workspace Root" : '"' + args.workspace + '"',
            "Sharpening RGB Frames" : bool(args.sharpening[0]),
            "RS Configuration File" : '"' + args.sconfig[0] + '"' if args.sconfig else '""'
            }

    elif args.mode == "reconstruct" :

        args.reconstruct = True

        parameters = {
            "Scanning Mode" : False,
            "Reconstruction Mode" : True,
            "Reconstruction Parameter File" : args.rconfig[0] ,
            "Mode" : "Local" if not bool(args.cloud[0]) else "Cloud based",
            "Cloud Configuration File" : '"' + args.cconfig[0] + '"' if args.cconfig else '""'
            }

        if args.cconfig :

            with open(parameters["Cloud Configuration File"]) as file :
                jsonFile = json.load(file)

            parameters["Address"] = jsonFile["Address"]
            parameters["Port"] = jsonFile["Port"]

        else :

            parameters["Address"] = args.address
            parameters["Port"] = args.port

    else :

        Logger.printError("Please use scan or reconstruct")
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
        rsr.writeReconstructionParametersFile()
        atexit.register(rsr.close)
        rsr.getDatasetDepthQuality()

    if parameters["Reconstruction Mode"] :

        if args.mode == "reconstruct" and parameters["Mode"] == "Local" :

            Logger.printOperationTitle("RECONSTRUCTING")

            reconstructor = Reconstructor.Reconstructor(parameters["Reconstruction Parameter File"])

        elif args.mode == "reconstruct" and parameters["Mode"] == "Cloud based" :

            Logger.printOperationTitle("RECONSTRUCTING")

            sk = Socket.Socket(parameters["Address"], parameters["Port"], parameters["Reconstruction Parameter File"].replace("rconfig.json", ""))
            sk.run()

        elif args.mode == "scan":

            rsr.close()

            Logger.printOperationTitle("RECONSTRUCTING")
            
            useCloud = input("Local reconstruction (0) or cloud based reconstruction (1) ?")

            if not useCloud :
                reconstructor = Reconstructor.Reconstructor(os.path.join(rsr.rootDir, "rconfig.json"))

            else :
                address = input("IP address ?")
                port = input("Port ?")
                folder = input("Dataset folder ?")

                sk = Socket.Socket(address, port, folder)
                sk.run()





if __name__ == "__main__" :
    main()
