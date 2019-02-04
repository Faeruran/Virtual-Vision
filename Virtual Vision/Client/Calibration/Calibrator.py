from open3d import *
import os
import sys
import numpy as np
import math
import time
import copy
sys.path.append("../Utils/")
from Logger import Logger
sys.path.append("./Detection/")
import Detector


class Calibrator :

    def pointsPicker(self, pc) :

        visualizer = VisualizerWithEditing()
        visualizer.create_window()
        visualizer.get_view_control().change_field_of_view(self.fovx)

        ctr = visualizer.get_view_control()
        param = ctr.convert_to_pinhole_camera_parameters()
        print(param.intrinsic.intrinsic_matrix)
        print(param.extrinsic)

        visualizer.add_geometry(pc)

        visualizer.run()

        visualizer.destroy_window()

        points = visualizer.get_picked_points()

        Logger.printSuccess("Successfully picked " + str(len(points)) + " !")

        return points



    def getManualTransformation(self, pointsIDMatrix) :

        transformer = TransformationEstimationPointToPoint()
        transformation = transformer.compute_transformation(self.pcWorld, self.pcPOV, Vector2iVector(pointsIDMatrix))
        Logger.printSuccess("Manual rough transformation successfully calculated !")

        return transformation



    def pointToPlaneICPRegistration(self, parameters, visualizer) :

        visualizer.add_geometry(self.pcWorld)
        visualizer.add_geometry(self.pcPOV)

        for i in range(parameters["Calibration Point To Plane ICP Iterations"]) :

            Logger.printProgress("Point to Plane ICP : " + str(i) + "/" + str(parameters["Calibration Point To Plane ICP Iterations"]))

            registration = registration_icp(self.pcWorld, self.pcPOV, parameters["Calibration Point To Plane ICP Distance Threshold"],
                np.identity(4),
                TransformationEstimationPointToPlane(),
                ICPConvergenceCriteria(max_iteration=parameters["Calibration Point To Plane Convergence Max Iterations"], relative_fitness=parameters["Calibration Point To Plane Convergence Relative Fitness"], relative_rmse=parameters["Calibration Point To Plane Convergence Relative RMSE"]))

            self.transform = np.dot(registration.transformation, self.transform)
            self.pcWorld.transform(registration.transformation)

            visualizer.update_geometry()
            visualizer.poll_events()
            visualizer.update_renderer()



    def coloredICPRegistration(self, parameters, visualizer) :

        visualizer.add_geometry(self.pcWorld)
        visualizer.add_geometry(self.pcPOV)

        for i in range(parameters["Calibration Colored ICP Iterations"]) :

            Logger.printProgress("Colored ICP : " + str(i) + "/" + str(parameters["Calibration Colored ICP Iterations"]))

            registration = registration_colored_icp(self.pcWorld, self.pcPOV, parameters["Calibration Colored ICP Distance Threshold"],
                np.identity(4),
                ICPConvergenceCriteria(max_iteration=parameters["Calibration Colored ICP Convergence Max Iterations"], relative_fitness=parameters["Calibration Colored ICP Convergence Relative Fitness"], relative_rmse=parameters["Calibration Colored ICP Convergence Relative RMSE"]))

            self.transform = np.dot(registration.transformation, self.transform)
            self.pcWorld.transform(registration.transformation)

            visualizer.update_geometry()
            visualizer.poll_events()
            visualizer.update_renderer()



    def __init__(self, parameters) :

        set_verbosity_level(VerbosityLevel.Error)

        Logger.printInfo("Loading point clouds ...")

        self.pcWorld = read_point_cloud(parameters["Calibration World Point Cloud Path"])
        self.pcPOV = read_point_cloud(parameters["Calibration POV Point Cloud Path"])

        self.pcWorld = voxel_down_sample(self.pcWorld, voxel_size=parameters["Calibration Voxel Size"])
        self.pcPOV = voxel_down_sample(self.pcPOV, voxel_size=parameters["Calibration Voxel Size"])

        estimate_normals(self.pcWorld, search_param=KDTreeSearchParamHybrid(radius=parameters["Calibration Normal Radius"], max_nn=parameters["Calibration Max NN"]))
        estimate_normals(self.pcPOV, search_param=KDTreeSearchParamHybrid(radius=parameters["Calibration Normal Radius"], max_nn=parameters["Calibration Max NN"]))

        Logger.printSuccess("Point clouds successfully loaded !")

        self.intrinsics = read_pinhole_camera_intrinsic(parameters["Calibration Intrinsics Path"])
        self.transform = np.identity(4)

        self.fovx = 2.0 * math.atan(self.intrinsics.width / (2.0 * self.intrinsics.get_focal_length()[0]))
        self.fovy = 2.0 * math.atan(self.intrinsics.height / (2.0 * self.intrinsics.get_focal_length()[1]))

        self.pcWorld.transform(np.asarray([
            [1, 0, 0, 0],
            [0, -1, 0, 0],
            [0, 0, -1, 0],
            [0, 0, 0, 1]
        ]))



        Logger.printInfo("Picking correspondence points for POV point cloud ...")
        pointsIDPOV = self.pointsPicker(self.pcPOV)
        Logger.printInfo("Picking correspondence points for world point cloud ...")
        pointsIDWorld = self.pointsPicker(self.pcWorld)

        if len(pointsIDWorld) != len(pointsIDPOV) :

            Logger.printError("The number of points selected during the two captures is different, quitting ...")
            exit()

        pointsIDMatrix = np.zeros((len(pointsIDWorld), 2))
        pointsIDMatrix[:,0] = pointsIDWorld
        pointsIDMatrix[:,1] = pointsIDPOV



        Logger.printInfo("Calculating a first transformation using the selected correspondence points ...")
        manualTransformation = self.getManualTransformation(pointsIDMatrix)

        self.pcWorld.transform(manualTransformation)
        self.transform = np.dot(manualTransformation, self.transform)

        visualizer = Visualizer()
        visualizer.create_window()

        Logger.printInfo("Aligning point clouds using Point to Plane ICP ...")
        self.pointToPlaneICPRegistration(parameters, visualizer)
        Logger.printSuccess("Successfully aligning point clouds using Point to Plane ICP !")
        Logger.printInfo("Aligning point clouds using Colored ICP ...")
        self.coloredICPRegistration(parameters, visualizer)
        Logger.printSuccess("Successfully aligning point clouds using Colored ICP !")

        visualizer.destroy_window()

        write_point_cloud(parameters["Detection World Point Cloud"], self.pcWorld)
