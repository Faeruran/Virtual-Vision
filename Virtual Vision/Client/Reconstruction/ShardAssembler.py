import numpy as np
from open3d import *
import os
import sys
import time
sys.path.append("../Utils/")
from Logger import Logger



class ShardAssembler(object) :

    def loadRGBD(self, convert) :

        colorPath = os.path.join(self.datasetPath, "Color")
        depthPath = os.path.join(self.datasetPath, "Depth")

        colorFileList = sorted(os.listdir(colorPath), key = lambda x : int(x.split(".jpg")[0]))
        depthFileList = sorted(os.listdir(depthPath), key = lambda x : int(x.split(".png")[0]))

        if len(colorFileList) != len(depthFileList) :

            Logger.printError("Color and Depth directories do not contain the same amount of pictures !")
            exit()

        temp = []

        for a in range(0, len(colorFileList)) :

            colorImage = read_image(os.path.join(colorPath, colorFileList[a]))
            depthImage = read_image(os.path.join(depthPath, depthFileList[a]))
            rgbd = create_rgbd_image_from_color_and_depth(colorImage, depthImage, depth_trunc=self.maxDepth, convert_rgb_to_intensity=convert)

            temp.append(rgbd)

        return temp



    def mergeShards(self) :

        rgbdDataset = self.loadRGBD(False)
        intrinsics = read_pinhole_camera_intrinsic(self.intrinsicsPath)

        volume = ScalableTSDFVolume(voxel_length=self.voxelLength, sdf_trunc=self.sdfTrunc, color_type=TSDFVolumeColorType.RGB8)

        totalOperations = sum([len(self.poseGraphsList[num].nodes) for num in range (0, len(self.poseGraph.nodes))])
        numOperations = 0

        for shardID in range(0, len(self.poseGraph.nodes)) :

            count = self.datasetSizes[shardID]
            frameID = 0

            for frameID in range(0, len(self.poseGraphsList[shardID].nodes)) :

                frame = rgbdDataset[count + frameID]
                pose = np.dot(self.poseGraph.nodes[shardID].pose, self.poseGraphsList[shardID].nodes[frameID].pose)
                volume.integrate(frame, intrinsics, np.linalg.inv(pose))
                Logger.printProgress("Merging shards " + str(int(float(numOperations / totalOperations) * 100)) + "% ...")
                numOperations += 1

        mesh = volume.extract_triangle_mesh()
        mesh.compute_vertex_normals()

        pcd = PointCloud()
        pcd.points = mesh.vertices
        pcd.colors = mesh.vertex_colors
        Logger.printInfo("Saving pointcloud ...")
        write_point_cloud(os.path.join(self.datasetPath, ("Result.ply")), pcd, False, False)
        Logger.printSuccess("Pointcloud successfully saved !")



    def updatePoseGraph(self, result) :

        blend = result[0]

        if blend["Odometry Case"] :

            self.origin = np.dot(result[2], self.origin)
            invertedOrigin = np.linalg.inv(self.origin)
            self.poseGraph.nodes.append(PoseGraphNode(invertedOrigin))
            self.poseGraph.edges.append(PoseGraphEdge(blend["ID A"], blend["ID B"], result[2], result[3], uncertain=False))

        else :

            self.poseGraph.edges.append(PoseGraphEdge(blend["ID A"], blend["ID B"], result[2], result[3], uncertain=True))



    def odometryRegistration(self, blend, maxIterations) :

        Logger.printProgress("Registrating shard " + str(blend["ID A"]) + " with shard " + str(blend["ID B"]))

        result = registration_colored_icp(self.shards[blend["ID A"]], self.shards[blend["ID B"]],
                self.voxelSize, blend["Transformation"],
                ICPConvergenceCriteria(relative_fitness = self.relativeFitness,
                relative_rmse = self.relativeRMSE, max_iteration = maxIterations))

        result = registration_icp(self.shards[blend["ID A"]], self.shards[blend["ID B"]], self.voxelSize * 0.4,
                result.transformation,
                TransformationEstimationPointToPlane())

        return result.transformation, get_information_matrix_from_point_clouds(self.shards[blend["ID A"]], self.shards[blend["ID B"]], self.voxelSize * 1.4, result.transformation)



    def loopClosureRegistration(self, blend) :

        Logger.printProgress("Registrating shard " + str(blend["ID A"]) + " with shard " + str(blend["ID B"]))

        result = registration_ransac_based_on_feature_matching(
                self.shards[blend["ID A"]], self.shards[blend["ID B"]], self.fpfhList[blend["ID A"]], self.fpfhList[blend["ID B"]],
                self.voxelSize * 1.4,
                TransformationEstimationPointToPoint(False), 4,
                [CorrespondenceCheckerBasedOnEdgeLength(self.correspondenceRatio),
                CorrespondenceCheckerBasedOnDistance(self.voxelSize * 1.4)],
                RANSACConvergenceCriteria(self.maxIterations, self.maxValidation))

        result = registration_icp(self.shards[blend["ID A"]], self.shards[blend["ID B"]], self.voxelSize * 0.4,
                result.transformation,
                TransformationEstimationPointToPlane())

        return True, result.transformation, get_information_matrix_from_point_clouds(self.shards[blend["ID A"]], self.shards[blend["ID B"]], self.voxelSize * 1.4, result.transformation)



    def process(self, blend) :

        if blend["Odometry Case"] :

            poseGraphA = self.poseGraphsList[blend["ID A"]]
            baseTransform = np.linalg.inv(poseGraphA.nodes[len(poseGraphA.nodes) - 1].pose)
            blend["Transformation"] = baseTransform
            transformation, information = self.odometryRegistration(blend, 50)

        else :

            success, transformation, information = self.loopClosureRegistration(blend)

            if not success :

                return False, np.identity(4), np.zeros((6,6))

        return True, transformation, information



    def loadPoseGraphs(self) :

        pgFileList = os.listdir(self.datasetPath)
        pgFileList = sorted([element for element in pgFileList if (".json" in element) and ("Shard" in element)])

        temp = []

        for pgFile in pgFileList :

            temp.append(read_pose_graph(os.path.join(self.datasetPath, pgFile)))

        return temp



    def loadBlends(self) :

        tempList = []

        for i in self.shards :

            for j in self.shards[self.shards.index(i) + 1 :] :

                temp = {
                    "ID A" : self.shards.index(i),
                    "ID B" : self.shards.index(j),
                    "Odometry Case" : True if (self.shards.index(j) - self.shards.index(i) == 1) else False
                }
                tempList.append(temp)

        return tempList



    def __init__(self, parameters, shards, datasetSizes) :

        set_verbosity_level(VerbosityLevel.Error)
        Logger.printSubOperationTitle("ASSEMBLING SHARDS")

        self.name = parameters["name"]
        self.datasetPath = parameters["datasetPath"]
        self.intrinsicsPath = parameters["intrinsicsPath"]
        self.minDepth = parameters["minDepth"]
        self.maxDepth = parameters["maxDepth"]
        self.voxelSize = parameters["voxelSize"]
        self.maxDepthDiff = parameters["maxDepthDiff"]
        self.voxelLength = parameters["voxelLength"]
        self.sdfTrunc = parameters["sdfTrunc"]
        self.correspondenceRatio = parameters["correspondenceRatio"]
        self.maxIterations = parameters["maxIterations"]
        self.maxValidation = parameters["maxValidation"]
        self.relativeFitness = parameters["relativeFitness"]
        self.relativeRMSE = parameters["relativeRMSE"]
        self.edgePruneThreshold = parameters["edgePruneThreshold"]
        self.preferenceLoopClosure = parameters["preferenceLoopClosure"]

        self.shards = shards
        self.datasetSizes = datasetSizes
        self.poseGraphsList = self.loadPoseGraphs()

        Logger.printInfo("Estimating normals and computing Fast Point Feature Histograms features (for " + str(len(self.shards)) + " shards) ...")
        [estimate_normals(shard, KDTreeSearchParamHybrid(radius=self.voxelSize * 2.0, max_nn=30)) for shard in self.shards]
        self.fpfhList = [compute_fpfh_feature(shard, KDTreeSearchParamHybrid(radius=self.voxelSize * 5.0, max_nn=100)) for shard in self.shards]
        Logger.printSuccess("Normals and FPFH successfully calculated !")


        self.blends = self.loadBlends()
        self.poseGraph = PoseGraph()
        self.origin = np.identity(4)

        self.poseGraph.nodes.append(PoseGraphNode(self.origin))

        self.results = []

        Logger.printInfo("Registrating shards ...")
        print(len(self.blends))

        for blend in self.blends :

            tempSuccess, tempTransformation, tempInformation = self.process(blend)

            if not blend["Odometry Case"] and not tempSuccess :

                self.results.append((blend, False, np.identity(4), np.identity(6)))

            else :

                self.results.append((blend, tempSuccess, tempTransformation, tempInformation))

        Logger.printSuccess("Shards successfully registered !")

        Logger.printInfo("Updating posegraph ...")

        for result in self.results :

            if result[1] :

                self.updatePoseGraph(result)

        Logger.printSuccess("Posegraph successfully updated !")

        Logger.printInfo("Optimizing posegraph ...")

        option = GlobalOptimizationOption(
                max_correspondence_distance = self.voxelSize * 1.4,
                edge_prune_threshold = self.edgePruneThreshold,
                preference_loop_closure = self.preferenceLoopClosure,
                reference_node = 0)

        global_optimization(self.poseGraph,
            GlobalOptimizationLevenbergMarquardt(),
            GlobalOptimizationConvergenceCriteria(), option)

        Logger.printSuccess("Posegraph successfully optimized !")

        Logger.printInfo("Merging shards ...")
        self.mergeShards()
        Logger.printSuccess("Shard successfully merged !")
