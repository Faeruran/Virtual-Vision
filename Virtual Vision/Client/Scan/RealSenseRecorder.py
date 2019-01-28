import os
import time
import pyrealsense2 as rs2
import keyboard
import numpy as np
import cv2
import json
import sys
import copy
sys.path.append("../Utils/")
from Logger import Logger



class RealSenseRecorder(object):

    def writeReconstructionParametersFile(self) :

        temp =  {
            "Name" : self.captureName,
            "Dataset Path" : self.rootDir,
            "Date" : self.captureName,
            "Intrinsics Path" : os.path.join(self.rootDir, "Intrinsics.json"),
            "Shard Size" : 70,
            "Min Depth" : 0.2,
            "Max Depth" : 1.8,
            "Voxel Size" : 0.03,
            "Max Depth Difference" : 0.07,
            "Edge Prune Threshold" : 0.25,
            "Preference Loop Closure" : 0.1,
            "Comparison Range" : 3,
            "Voxel Length" : (3.0/512.0),
            "SDF Trunc" : 0.04,
            "Volume Unit Resolution" : 16,
            "Depth Sampling Stride" : 4,
            "Correspondence Ratio" : 0.9,
            "Max Iterations" : 4000000,
            "Max Validation" : 500,
            "Relative Fitness" : 1e-6,
            "Relative RMSE" : 1e-6,
            "Dataset Size" : self.datasetSize
        }

        with open(os.path.join(self.rootDir, "rconfig.json"), "w") as jsonFile :
            json.dump(temp, jsonFile, indent=4)



    def rgbdErrorSuperposition(self, rgb, d) :

        rgbdErrorSuperposed = rgb
        print(d.shape)
        for x in range(0, self.height) :
            for y in range(0, self.width) :

                if d[x][y] == 0 :
                    rgbdErrorSuperposed[x][y] = [0, 0, 255]

        return rgbdErrorSuperposed



    def exportIntrinsics(self) :

        #Exports a JSON file, following the template provided by Open3D, which contains the intrinsics of the RealSense
        temp = {
            "width" : self.width,
            "height" : self.height,
            "intrinsic_matrix" : [self.intrinsics.fx, 0, 0, 0, self.intrinsics.fy, 0, self.intrinsics.ppx, self.intrinsics.ppy, 1]
            }

        with open(os.path.join(self.rootDir, "Intrinsics.json"), "w") as jsonFile :
            json.dump(temp, jsonFile)



    def imageSharpener(self, blurryImage) :

        #Sharpens a blurry image and returns it
        kernel = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
        return cv2.filter2D(blurryImage, -1, kernel)



    def setupFolder(self) :

        #Setup a new scan directory within the workspace (the name of the main directory will be the epoch time at the time of the creation)
        self.captureName = str(int(time.time()))
        self.rootDir = os.path.join(self.rootDir, ("RSCapture-" + self.captureName))
        os.makedirs(self.rootDir)
        os.makedirs(os.path.join(self.rootDir, "Depth"))
        os.makedirs(os.path.join(self.rootDir, "Color"))
        self.exportIntrinsics()
        Logger.printInfo("Using workspace : " + '"' + self.rootDir + '"')



    def getDatasetDepthQuality(self) :

        Logger.printInfo("Analyzing depth frames quality ...")

        depthPath = os.path.join(self.rootDir, "Depth")
        depthFileList = sorted(os.listdir(depthPath), key = lambda x : int(x.split(".png")[0]))

        depthDataset = []

        for file in depthFileList :
            depthDataset.append(cv2.imread(os.path.join(os.path.join(self.rootDir, "Depth"), file), -1))

        mean = 0.0
        numPixel = self.height * self.width
        count = 0

        for frame in depthDataset :

            frameQuality = 0.0
            Logger.printProgress("[Dataset Analysis] Frame " + str(count) + "/" + str(len(depthDataset)) + " -> " + str(round((float(count) * 100.0) / len(depthDataset), 2)) + "%")

            for x in range(self.height) :

                for y in range(self.width) :

                    if frame[x][y] > 0 :

                        frameQuality += 1

            frameQuality = frameQuality / numPixel
            mean += frameQuality

            count += 1

        mean = mean / len(depthDataset)

        Logger.printSuccess("Average depth coverage : " + str(mean))



    def scan(self) :

        #Depending on the --nsec argument set by the user, this function will get, process and save the frames taken by the RealSense
        #This function will use a timer or just wait for the user to press Q
        #The depth images will be saved in a "Depth" directory, while the RGB frames will be saved within the "Color" directory
        #If sharpening is enabled, a sharpened copy of each RGB frame will be saved with the "-sharp" extension

        #decimationFilter = rs2.decimation_filter()
        #decimationFilter.set_option(rs2.option.filter_magnitude, 2)

        depthDisparityFilter = rs2.disparity_transform(True)

        disparityDepthfilter = rs2.disparity_transform(False)

        spatialFilter = rs2.spatial_filter()
        spatialFilter.set_option(rs2.option.filter_magnitude, 5)
        spatialFilter.set_option(rs2.option.filter_smooth_alpha, 1)
        spatialFilter.set_option(rs2.option.filter_smooth_delta, 50)
        #spatialFilter.set_option(rs2.option.holes_fill, 3)

        temporalFilter = rs2.temporal_filter()
        temporalFilter.set_option(rs2.option.filter_smooth_alpha, 0.4)
        temporalFilter.set_option(rs2.option.filter_smooth_delta, 50)

        holeFillingFilter = rs2.hole_filling_filter()
        holeFillingFilter.set_option(rs2.option.holes_fill, 2)

        counter = 0
        modulo = 0

        if self.scanDuration :

            Logger.printInfo(str(self.scanDuration) + " seconds scanner started !")

            initTime = time.time()

            while time.time() - initTime < float(self.scanDuration) :

                depthFrame, colorFrame = self.getFrame()
                depthImage = np.asanyarray(depthFrame.data)
                colorImage = np.asanyarray(colorFrame.data)
                depthPath = os.path.join(os.path.join(self.rootDir, "Depth"), (str(counter) + ".png"))
                colorPath = os.path.join(os.path.join(self.rootDir, "Color"), (str(counter) + ".jpg"))

                if modulo % 2 == 0 :

                    frame = depthFrame
                    #frame = decimationFilter.process(frame)
                    frame = depthDisparityFilter.process(frame)
                    frame = spatialFilter.process(frame)
                    frame = temporalFilter.process(frame)
                    frame = disparityDepthfilter.process(frame)

                    self.datasetSize += 1

                    cv2.imwrite(depthPath, np.asanyarray(frame.data))
                    cv2.imwrite(colorPath, colorImage)

                    if self.sharpening :

                        sharpColorPath = os.path.join(os.path.join(self.rootDir, "Color"), (str(counter) + "-sharp.jpg"))
                        #sharpDepthPath = os.path.join(os.path.join(self.rootDir, "Depth"), (str(counter) + "-sharp.png"))

                        cv2.imwrite(sharpColorPath, self.imageSharpener(colorImage))
                        #cv2.imwrite(sharpDepthPath, self.imageSharpener(depthImage))

                    counter += 1

                cv2.imshow("Capture", colorImage)
                cv2.waitKey(1)

                modulo += 1

            Logger.printSuccess("End of scan !")

        else :

            Logger.printInfo("Scanner started ! Press Q to end the capture !")

            while not keyboard.is_pressed("q") :

                depthFrame, colorFrame = self.getFrame()
                depthImage = np.asanyarray(depthFrame.data)
                colorImage = np.asanyarray(colorFrame.data)
                depthPath = os.path.join(os.path.join(self.rootDir, "Depth"), (str(counter) + ".png"))
                colorPath = os.path.join(os.path.join(self.rootDir, "Color"), (str(counter) + ".jpg"))

                if modulo % 2 == 0 :

                    frame = depthFrame
                    #frame = decimationFilter.process(frame)
                    frame = depthDisparityFilter.process(frame)
                    frame = spatialFilter.process(frame)
                    frame = temporalFilter.process(frame)
                    frame = disparityDepthfilter.process(frame)

                    self.datasetSize += 1

                    cv2.imwrite(depthPath, np.asanyarray(frame.data))
                    cv2.imwrite(colorPath, colorImage)

                    if self.sharpening :

                        sharpColorPath = os.path.join(os.path.join(self.rootDir, "Color"), (str(counter) + "-sharp.jpg"))
                        #sharpDepthPath = os.path.join(os.path.join(self.rootDir, "Depth"), (str(counter) + "-sharp.png"))

                        cv2.imwrite(sharpColorPath, self.imageSharpener(colorImage))
                        #cv2.imwrite(sharpDepthPath, self.imageSharpener(depthImage))

                    counter += 1


                cv2.imshow("Capture", colorImage)
                cv2.waitKey(1)

                modulo += 1

            Logger.printSuccess("End of scan !")



    def getFrame(self) :

        #Get, align and return frames obtained from the RealSense
        frames = self.pipeline.wait_for_frames()
        alignedFrames = self.aligner.process(frames)

        depthFrame = alignedFrames.get_depth_frame()
        colorFrame = alignedFrames.get_color_frame()

        if depthFrame and colorFrame :

            return depthFrame, colorFrame

        return None



    def close(self) :

        #Close the pipeline
        Logger.printInfo("Closing scanner ...")
        try :
            self.depthSensor.stop()
            self.pipeline.stop()
        except :
            pass

        cv2.destroyAllWindows()
        Logger.printSuccess("Scanner successfully closed !")
        #time.sleep(5)
        self.closed = True



    def __init__(self, scanDuration, rootDir, sharpening, configFile, fps, width, height, visualPreset, laserPower, exposure, gain) :

        self.scanDuration = scanDuration
        self.fps = fps
        self.rootDir = rootDir
        self.sharpening = sharpening
        self.width = width
        self.height = height
        self.configFile = configFile
        self.captureName = None
        self.closed = False

        if self.configFile :

            try :

                with open(self.configFile) as file:

                        configString = json.load(file)
                        configDict = configString
                        configString = json.dumps(configString)

                        self.fps = int(configDict["stream-fps"])
                        self.width = int(configDict["stream-width"])
                        self.height = int(configDict["stream-height"])

                        Logger.printSuccess("Parameters successfully loaded !")

            except :

                Logger.printError("Could not read the RealSense configuration file")

        self.window = cv2.namedWindow("Capture", cv2.WINDOW_AUTOSIZE)

        Logger.printInfo("Initializing scanner ...")

        try :

            #Initialization
            self.pipeline = rs2.pipeline()
            self.config = rs2.config()
            #Enable streams
            self.config.enable_stream(rs2.stream.depth, self.width, self.height, rs2.format.z16, self.fps)
            self.config.enable_stream(rs2.stream.color, self.width, self.height, rs2.format.bgr8, self.fps)
            #Start streaming
            self.profile = self.pipeline.start(self.config)

        except Exception as e :

            Logger.printError("Unable to start the stream, gonna quit.\nException -> " + str(e))
            exit()



        self.device = self.profile.get_device()
        self.depthSensor = self.device.first_depth_sensor()

        try :

            #Set parameters

            if configFile :

                advancedMode = rs2.rs400_advanced_mode(self.device)

                print(configString)
                advancedMode.load_json(json_content=configString)

            else :

                """
                0 -> Custom
                1 -> Default
                2 -> Hand
                3 -> High Accuracy
                4 -> High Density
                5 -> Medium Density
                """
                self.depthSensor.set_option(rs2.option.visual_preset, visualPreset)
                self.depthSensor.set_option(rs2.option.laser_power, laserPower)
                self.depthSensor.set_option(rs2.option.gain, gain)
                self.depthSensor.set_option(rs2.option.exposure, exposure)
                #self.depthSensor.set_option(rs2.option.max_distance, 4.0)

        except Exception as e :

            Logger.printError("Unable to set one parameter on the RealSense, gonna continue to run.\nException -> " + str(e))
            pass

        self.intrinsics = self.profile.get_stream(rs2.stream.depth).as_video_stream_profile().get_intrinsics()

        #Create an align object -> aligning depth frames to color frames
        self.aligner = rs2.align(rs2.stream.color)

        Logger.printSuccess("Scanner successfully initialized !")
        self.datasetSize = 0
        self.depthDataset = []
