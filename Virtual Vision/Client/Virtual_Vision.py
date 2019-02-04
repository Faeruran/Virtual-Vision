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
sys.path.append("./Calibration/")
import Calibrator
sys.path.append("./Detection/")
import Detector


def main() :

    os.system("clear")

    rootDir = os.path.join(os.path.join(os.path.join(os.environ["HOME"]), "Bureau"), "Workspace")

    parser = argparse.ArgumentParser(description="Virtual Vision v0.1 - Client")
    modes = parser.add_subparsers(title = "Operating Mode", dest="mode", help="Scan, Reconstruct or Cloud")
    scanParser = modes.add_parser("scan", help="Scanning mode")
    scanLoadGroup = scanParser.add_argument_group(title="Automatic Configuration (JSON importation)")
    scanManualGroup = scanParser.add_argument_group(title="Manual Settings")
    reconstructParser = modes.add_parser("reconstruct", help="Reconstruction mode")
    cloudParser = modes.add_parser("cloud", help="Cloud based interaction and processing")
    calibrationParser = modes.add_parser("calibration", help="Depth camera calibration for real time 3D integration")
    detectionParser = modes.add_parser("detection", help="Real time detection and 3D integration")


    scanParser.add_argument("--nsec", action="store", nargs=1, default=[0], type=int, required=False, help="Scan duration in seconds (0 for unlimited, press Q to quit). Default : 0")
    scanParser.add_argument("--workspace", action="store", nargs=1, default=rootDir, type=str, required=False, help="Path of the workspace, where the dataset will be saved. Default : 'USER/Desktop/Workspace'")
    scanParser.add_argument("--sharpening", action="store", nargs=1, default=[0], type=int, required=False, help="Allows to sharpen the images in order to reduce the impact of the motion blur. Default : 0")
    scanParser.add_argument("--autoreconstruct", action="store", nargs=1, default=[0], type=int, required=False, help="Automatically reconstruct the dataset after the scan. Default : 1")
    scanParser.add_argument("--depthanalysis", action="store", nargs=1, default=[0], type=int, required=False, help="Process the dataset in order to estimate the coverage of the depth frames. Default : 0")

    scanLoadGroup.add_argument("--sconfig", action="store", nargs=1, type=str, required=False, help="Import a JSON RealSense configuration file (instead of Manual Settings, can be generated using the RealSense SDK) : path")

    scanManualGroup.add_argument("--fps", action="store", nargs=1, default=[60], type=int, required=False, help="Framerate of the capture (higher can reduce motion blur). Default : 60")
    scanManualGroup.add_argument("--width", action="store", nargs=1, default=[848], type=int, required=False, help="Width of the captured frames. Default : 848")
    scanManualGroup.add_argument("--height", action="store", nargs=1, default=[480], type=int, required=False, help="Height of the captured frames. Default : 480")
    scanManualGroup.add_argument("--vpreset", action="store", nargs=1, default=[0], type=int, required=False, help="Allows to choose some preset settings provided by the RealSense SDK (0 -> Custom, 1 -> Default, 2 -> Hand, 3 -> High Accuracy, 4 -> High Density, 5 -> Medium Density). Default 0 (custom)")
    scanManualGroup.add_argument("--laserpower", action="store", nargs=1, default=[240], type=int, required=False, help="RealSense laser power. Default : 240")
    scanManualGroup.add_argument("--exposure", action="store", nargs=1, default=[3200], type=int, required=False, help="Exposure time of the RealSense sensor. Default : 3200")
    scanManualGroup.add_argument("--gain", action="store", nargs=1, default=[16], type=int, required=False, help="RealSense sensor gain. Default : 16")

    reconstructParser.add_argument("--rconfig", action="store", nargs=1, default="", type=str, required=True, help="Import a JSON dataset reconstruction settings file : path")

    cloudParser.add_argument("--address", action="store", nargs=1, default=[], type=str, required=False, help="Cloud server's IP address.")
    cloudParser.add_argument("--port", action="store", nargs=1, default=[], type=str, required=False, help="Cloud server's port.")
    cloudParser.add_argument("--reconstruct", action="store", nargs=1, default=[], type=str, required=False, help="Cloud based reconstruction, using the specified reconstruction settings file : path")
    cloudParser.add_argument("--list", action="store", nargs=1, default=[0], type=int, required=False, help="Displays the name of the dataset present on the cloud.")
    cloudParser.add_argument("--remove", action="store", nargs=1, default=[], type=str, required=False, help="Removes one dataset present on the cloud by specifying its name")
    cloudParser.add_argument("--getresult", action="store", nargs=1, default=[], type=str, required=False, help="Downloads the point cloud of the specified reconstructed dataset (name)")
    cloudParser.add_argument("--mergeshards", action="store", nargs=1, default=[], type=str, required=False, help="Merges the shards of the specified dataset (name). Works only if the reconstruction ended before successfully merging the shards")

    args = parser.parse_args()

    if args.mode == "scan" :

        parameters = {
            "Scanning Mode" : True,
            "Reconstruction Mode" : bool(args.autoreconstruct[0]),
            "Cloud Mode" : False,
            "Calibration Mode" : False,
            "Detection Mode" : False,
            "Scan Duration (s)" : args.nsec[0],
            "Workspace Root" : '"' + args.workspace + '"',
            "Sharpening RGB Frames" : bool(args.sharpening[0]),
            "RS Configuration File" : '"' + args.sconfig[0] + '"' if args.sconfig else '""',
            "Depth Analysis" : bool(args.depthanalysis[0])
            }



    elif args.mode == "reconstruct" :

        parameters = {
            "Scanning Mode" : False,
            "Reconstruction Mode" : True,
            "Cloud Mode" : False,
            "Calibration Mode" : False,
            "Detection Mode" : False,
            "Reconstruction Parameter File" : args.rconfig[0]
            }



    elif args.mode == "cloud" :

        parameters = {
            "Scanning Mode" : False,
            "Reconstruction Mode" : False,
            "Cloud Mode" : True,
            "Calibration Mode" : False,
            "Detection Mode" : False
            }

        if args.address and args.port :

            parameters["Address"] = args.address[0]
            parameters["Port"] = args.port[0]

        else :

            with open("config.json") as file :
                jsonFile = json.load(file)

                parameters["Address"] = jsonFile["Cloud Address"]
                parameters["Port"] = jsonFile["Cloud Port"]

        if args.reconstruct :
            parameters["Operation"] = "Reconstruction"
            parameters["Reconstruction Parameter File"] = args.reconstruct[0]

        elif args.list[0] :
            parameters["Operation"] = "List"

        elif args.remove :
            parameters["Operation"] = "Remove"
            parameters["Dataset To Remove"] = args.remove[0]

        elif args.getresult :
            parameters["Operation"] = "Download Result"
            parameters["Dataset Result To Download"] = args.getresult[0]

        elif args.mergeshards :
            parameters["Operation"] = "Merge Shards"
            parameters["Dataset Shards To Merge"] = args.mergeshards[0]

        else :
            Logger.printError("No operation selected, quitting ...")
            exit()



    elif args.mode == "calibration" :

        parameters = {
            "Scanning Mode" : False,
            "Reconstruction Mode" : False,
            "Cloud Mode" : False,
            "Calibration Mode" : True,
            "Detection Mode" : False
            }

        with open("config.json") as file :
            jsonFile = json.load(file)

            parameters["Calibration World Point Cloud Path"] = jsonFile["Calibration World Point Cloud Path"]
            parameters["Calibration POV Point Cloud Path"] = jsonFile["Calibration POV Point Cloud Path"]
            parameters["Calibration Intrinsics Path"] = jsonFile["Calibration Intrinsics Path"]
            parameters["Calibration Voxel Size"] = float(jsonFile["Calibration Voxel Size"])
            parameters["Calibration Normal Radius"] = float(jsonFile["Calibration Normal Radius"])
            parameters["Calibration Max NN"] = int(jsonFile["Calibration Max NN"])
            parameters["Calibration Point To Plane ICP Iterations"] = int(jsonFile["Calibration Point To Plane ICP Iterations"])
            parameters["Calibration Colored ICP Iterations"] = int(jsonFile["Calibration Colored ICP Iterations"])
            parameters["Calibration Point To Plane ICP Distance Threshold"] = float(jsonFile["Calibration Point To Plane ICP Distance Threshold"])
            parameters["Calibration Colored ICP Distance Threshold"] = float(jsonFile["Calibration Colored ICP Distance Threshold"])
            parameters["Calibration Point To Plane Convergence Max Iterations"] = int(jsonFile["Calibration Point To Plane Convergence Max Iterations"])
            parameters["Calibration Colored ICP Convergence Max Iterations"] = int(jsonFile["Calibration Colored ICP Convergence Max Iterations"])
            parameters["Calibration Point To Plane Convergence Relative Fitness"] = float(jsonFile["Calibration Point To Plane Convergence Relative Fitness"])
            parameters["Calibration Colored ICP Convergence Relative Fitness"] = float(jsonFile["Calibration Colored ICP Convergence Relative Fitness"])
            parameters["Calibration Point To Plane Convergence Relative RMSE"] = float(jsonFile["Calibration Point To Plane Convergence Relative RMSE"])
            parameters["Calibration Colored ICP Convergence Relative RMSE"] = float(jsonFile["Calibration Colored ICP Convergence Relative RMSE"])
            parameters["Detection World Point Cloud"] = jsonFile["Detection World Point Cloud"]



    elif args.mode == "detection" :

        parameters = {
            "Scanning Mode" : False,
            "Reconstruction Mode" : False,
            "Cloud Mode" : False,
            "Calibration Mode" : False,
            "Detection Mode" : True
            }

        with open("config.json") as file :
            jsonFile = json.load(file)

            parameters["Detection Realsense Configuration File Path"] = jsonFile["Detection Realsense Configuration File Path"]
            parameters["Detection Darknet GPU ID"] = int(jsonFile["Detection Darknet GPU ID"])
            parameters["Detection Darknet Model Configuration File Path"] = jsonFile["Detection Darknet Model Configuration File Path"]
            parameters["Detection Darknet Model Weights File Path"] = jsonFile["Detection Darknet Model Weights File Path"]
            parameters["Detection Darknet Model Meta File Path"] = jsonFile["Detection Darknet Model Meta File Path"]
            parameters["Detection Darknet Model Labels File Path"] = jsonFile["Detection Darknet Model Labels File Path"]
            parameters["Detection Label To Detect"] = jsonFile["Detection Label To Detect"]
            parameters["Detection World Point Cloud"] = jsonFile["Detection World Point Cloud"]
            parameters["Project Root Path"] = jsonFile["Project Root Path"]
            parameters["Calibration Voxel Size"] = float(jsonFile["Calibration Voxel Size"])
            parameters["Calibration Normal Radius"] = float(jsonFile["Calibration Normal Radius"])
            parameters["Calibration Max NN"] = int(jsonFile["Calibration Max NN"])



    else :

        Logger.printError("Please use scan, reconstruct or cloud")
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
        if parameters["Depth Analysis"] :
            rsr.getDatasetDepthQuality()




    if parameters["Reconstruction Mode"] :

        if args.mode == "reconstruct" :

            Logger.printOperationTitle("RECONSTRUCTING")

            reconstructor = Reconstructor.Reconstructor(parameters["Reconstruction Parameter File"])

        elif args.mode == "scan":

            rsr.close()

            Logger.printOperationTitle("RECONSTRUCTING")

            reconstructor = Reconstructor.Reconstructor(os.path.join(rsr.rootDir, "rconfig.json"))


    if parameters["Cloud Mode"] :

        sk = Socket.Socket(parameters)

    if parameters["Calibration Mode"] :

        calibrator = Calibrator.Calibrator(parameters)

    if parameters["Detection Mode"] :

        detector = Detector.Detector(parameters)
        detector.run(parameters)



if __name__ == "__main__" :
    main()
