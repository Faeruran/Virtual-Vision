import os
import time
import pyrealsense2 as rs2
from open3d import *
import numpy as np
import cv2
import json
import sys
import darknet
import random
sys.path.append("../Utils/")
from Logger import Logger

class Detector :

    def addTranslatedSquare(self, visualizer, x, y, z) :

        square = create_mesh_box(width = 0.08, height = 0.08, depth = 0.08)
        square.compute_vertex_normals()
        square.paint_uniform_color([0.9, 0.1, 0.1])

        transform = np.asarray([
            [1, 0, 0, x + 0.025],
            [0, -1, 0, y + 0.025],
            [0, 0, -1, z + 0.025],
            [0, 0, 0, 1]
        ])

        square.transform(transform)

        visualizer.add_geometry(square)

        visualizer.update_geometry()
        visualizer.poll_events()
        visualizer.update_renderer()

        return square, transform



    def postProcessDepthFrame(self, frame) :

        frame = self.depthDisparityFilter.process(frame)
        frame = self.spatialFilter.process(frame)
        frame = self.temporalFilter.process(frame)
        frame = self.disparityDepthfilter.process(frame)

        return frame



    def getFrame(self) :

        #Get, align and return frames obtained from the RealSense
        frames = self.pipeline.wait_for_frames()
        alignedFrames = self.aligner.process(frames)

        depthFrame = alignedFrames.get_depth_frame()
        colorFrame = alignedFrames.get_color_frame()

        if depthFrame and colorFrame :

            return depthFrame, colorFrame

        return None



    def getRandColorList(self) :

        temp = []

        for i in range(256) :

            color = [random.randrange(0, 256), random.randrange(0, 256), random.randrange(0, 256)]
            temp.append([color])

        return temp



    def detect(self, parameters) :

        depthFrame, colorFrame = self.getFrame()
        depthFrame = self.postProcessDepthFrame(depthFrame)
        depthImage = np.asanyarray(depthFrame.data)
        colorImage = np.asanyarray(colorFrame.data)

        cv2.imwrite(os.path.join(parameters["Project Root Path"], "Detection/temp.jpg"), colorImage)
        res = darknet.detect(self.net, self.meta, os.path.join(parameters["Project Root Path"], "Detection/temp.jpg").encode("UTF-8"))
        #cv2.circle(colorImage, (int(colorImage.shape[1] / 2), int(colorImage.shape[0] / 2)), 10, (0,0,255), -1)
        point = []
        objectList = []

        for element in res :

            if element[0].decode("UTF-8") == parameters["Detection Label To Detect"] :

                cv2.circle(colorImage, (int(element[2][0]), int(element[2][1])), 10, (255,0,0), -1)

                distance = depthImage[int(element[2][1])][int(element[2][0])]
                depthIntrinsics = depthFrame.profile.as_video_stream_profile().intrinsics
                depthPixel = [int(element[2][0]), int(element[2][1])]

                point = rs2.rs2_deproject_pixel_to_point(self.intrinsics, depthPixel, distance)
                while len(point) == 0 :
                    point = rs2.rs2_deproject_pixel_to_point(self.intrinsics, depthPixel, distance)

        cv2.imshow("Capture", colorImage)
        cv2.waitKey(1)

        return point



    def run(self, parameters) :

        self.pcWorld = read_point_cloud(parameters["Detection World Point Cloud"])
        self.pcWorld.purge()
        self.pcWorld = voxel_down_sample(self.pcWorld, voxel_size=parameters["Calibration Voxel Size"])
        estimate_normals(self.pcWorld, search_param=KDTreeSearchParamHybrid(radius=parameters["Calibration Normal Radius"], max_nn=parameters["Calibration Max NN"]))

        visualizer = Visualizer()
        visualizer.create_window()
        visualizer.add_geometry(self.pcWorld)

        coordinates = self.detect(parameters)

        while len(coordinates) < 3 :
            coordinates = self.detect(parameters)

        temp = [coordinates[0] / 1000, coordinates[1] / 1000, coordinates[2] / 1000]
        old = temp

        square, transformSquare = self.addTranslatedSquare(visualizer, temp[0], temp[1], temp[2])
        """
        ctr = visualizer.get_view_control()
        param = ctr.convert_to_pinhole_camera_parameters()
        print(param.intrinsic.intrinsic_matrix)
        print(param.extrinsic)
        """

        while(True) :

            coordinates = self.detect(parameters)
            if len(coordinates) == 3 :

                temp = [coordinates[0] / 1000, coordinates[1] / 1000, coordinates[2] / 1000]

                if temp != [0, 0, 0] :

                    transform = np.asarray([
                        [1, 0, 0, temp[0] - old[0]],
                        [0, 1, 0, temp[1] - old[1]],
                        [0, 0, 1, temp[2] - old[2]],
                        [0, 0, 0, 1]
                    ])

                    old = temp
                    square.transform(transform)

            visualizer.update_geometry()
            visualizer.poll_events()
            visualizer.update_renderer()



        visualizer.destroy_window()
        cv2.destroyAllWindows()



    def __init__(self, parameters) :

        try :

            with open(parameters["Detection Realsense Configuration File Path"]) as file:

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

            advancedMode = rs2.rs400_advanced_mode(self.device)
            advancedMode.load_json(json_content=configString)

        except Exception as e :

            Logger.printError("Unable to set one parameter on the RealSense, gonna continue to run.\nException -> " + str(e))
            pass

        #Create an align object -> aligning depth frames to color frames
        self.aligner = rs2.align(rs2.stream.color)

        self.intrinsics = self.profile.get_stream(rs2.stream.depth).as_video_stream_profile().get_intrinsics()

        Logger.printSuccess("Scanner successfully initialized !")



        self.depthDisparityFilter = rs2.disparity_transform(True)

        self.disparityDepthfilter = rs2.disparity_transform(False)

        self.spatialFilter = rs2.spatial_filter()
        self.spatialFilter.set_option(rs2.option.filter_magnitude, 5)
        self.spatialFilter.set_option(rs2.option.filter_smooth_alpha, 1)
        self.spatialFilter.set_option(rs2.option.filter_smooth_delta, 50)
        #self.spatialFilter.set_option(rs2.option.holes_fill, 3)

        self.temporalFilter = rs2.temporal_filter()
        self.temporalFilter.set_option(rs2.option.filter_smooth_alpha, 0.4)
        self.temporalFilter.set_option(rs2.option.filter_smooth_delta, 50)

        self.holeFillingFilter = rs2.hole_filling_filter()
        self.holeFillingFilter.set_option(rs2.option.holes_fill, 2)

        darknet.set_gpu(parameters["Detection Darknet GPU ID"])
        self.net = darknet.load_net(parameters["Detection Darknet Model Configuration File Path"].encode("UTF-8"), parameters["Detection Darknet Model Weights File Path"].encode("UTF-8"), 0)
        self.meta = darknet.load_meta(parameters["Detection Darknet Model Meta File Path"].encode("UTF-8"))

        with open(parameters["Detection Darknet Model Labels File Path"], "r") as file :
            self.classes = [line.strip() for line in file.readlines()]

        self.colorSet = self.getRandColorList()
