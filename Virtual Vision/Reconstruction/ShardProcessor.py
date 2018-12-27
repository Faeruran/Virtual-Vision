from open3d import *
import opencv_pose_estimation as ope
import os
import sys
import time
sys.path.append("../Utils/")
from Logger import Logger



class ShardProcessor(object) :

    def poseGraphToPointCloud(self) :

        volume = ScalableTSDFVolume(voxel_length = self.voxelLength, sdf_trunc = self.sdfTrunc, color_type = TSDFVolumeColorType.RGB8, volume_unit_resolution=self.volumeUnitResolution, depth_sampling_stride=self.depthSamplingStride)

        for i in range(0, len(self.poseGraph.nodes)) :

            tempPose = self.poseGraph.nodes[i].pose
            volume.integrate(self.rgbdDatasetRGB[i], self.intrinsics, np.linalg.inv(tempPose))
            Logger.printProgress("[Shard " + str(self.id) + "] " + str(int(float(i / len(self.poseGraph.nodes)) * 100)) + "% " + str(i) + " x " + str(len(self.poseGraph.nodes)))
        Logger.printProgress("[Shard " + str(self.id) + "] Extracting triangles ...")
        mesh = volume.extract_triangle_mesh()
        Logger.printProgress("[Shard " + str(self.id) + "] Computing normals ...")
        mesh.compute_vertex_normals()

        pcd = PointCloud()
        pcd.points = mesh.vertices
        pcd.colors = mesh.vertex_colors
        Logger.printInfo("[Shard " + str(self.id) + "] Saving point cloud as " + os.path.join(self.datasetPath, ("Shard" + str(self.id) + "-" + str(int(time.time())))) + ".ply")
        fileName = "Shard" + str(self.id) + "-" + str(int(time.time()))
        write_point_cloud(os.path.join(self.datasetPath, (fileName + ".ply")), pcd, False, False)
        write_pose_graph(os.path.join(self.datasetPath, (fileName + ".json")), self.poseGraph)
        Logger.printSuccess("[Shard " + str(self.id) + "] Point cloud successfully saved !")



    def pairRegistration(self, pcNumA, pcNumB) :

        pcSource = self.pcDataset[pcNumA]
        pcTarget = self.pcDataset[pcNumB]

        if abs(pcNumA - pcNumB) > 1 :

            success, odometryInit = ope.pose_estimation(self.rgbdDataset[pcNumA], self.rgbdDataset[pcNumB], self.intrinsics, False)

            if success :

                [success, trans, info] = compute_rgbd_odometry(self.rgbdDataset[pcNumA], self.rgbdDataset[pcNumB], self.intrinsics, odometryInit, RGBDOdometryJacobianFromHybridTerm(), self.odometryOption)

                return [success, trans, info]

            else :

                return [False, np.identity(4), np.identity(6)]

        else :

            [success, trans, info] = compute_rgbd_odometry(self.rgbdDataset[pcNumA], self.rgbdDataset[pcNumB], self.intrinsics, np.identity(4), RGBDOdometryJacobianFromHybridTerm(), self.odometryOption)

            return [success, trans, info]



    def registration(self) :

        odometryMatrix = np.identity(4)
        self.poseGraph.nodes.append(PoseGraphNode(odometryMatrix))

        for pcNumA in range(0, len(self.pcDataset)) :

            for pcNumB in range(pcNumA + 1, len(self.pcDataset)) :

                if pcNumB == pcNumA + 1 :

                    [success, trans, info] = self.pairRegistration(pcNumA, pcNumB)

                    odometryMatrix = np.dot(trans, odometryMatrix)
                    odometryMatrixInv = np.linalg.inv(odometryMatrix)

                    self.poseGraph.nodes.append(PoseGraphNode(odometryMatrixInv))
                    self.poseGraph.edges.append(PoseGraphEdge(pcNumA, pcNumB, trans, info, uncertain=False))

                    Logger.printProgress("[Shard " + str(self.id) + "] " + str(int(float(pcNumA / len(self.pcDataset)) * 100)) + "% " + str(pcNumA + self.minID) + " x " + str(pcNumB + self.minID))

                elif pcNumB - pcNumA < self.comparisonRange :

                    [success, trans, info] = self.pairRegistration(pcNumA, pcNumB)
                    if success :

                        self.poseGraph.edges.append(PoseGraphEdge(pcNumA, pcNumB, trans, info, uncertain = True))

                        Logger.printProgress("[Shard " + str(self.id) + "] " + str(int(float(pcNumA / len(self.pcDataset)) * 100)) + "% " + str(pcNumA + self.minID) + " x " + str(pcNumB + self.minID))

                """
                if pcNumA % 5 == 0 and pcNumB % 5 == 0 :

                    [success, trans, info] = self.pairRegistration(pcNumA, pcNumB)
                    if success :

                        self.poseGraph.edges.append(PoseGraphEdge(pcNumA, pcNumB, trans, info, uncertain = True))

                        Logger.printProgress("[Shard " + str(self.id) + "] " + str(int(float(pcNumA / len(self.pcDataset)) * 100)) + "% " + str(pcNumA + self.minID) + " x " + str(pcNumB + self.minID))
                """

        option = GlobalOptimizationOption(
                max_correspondence_distance = self.maxDepthDiff,
                edge_prune_threshold = self.edgePruneThreshold,
                preference_loop_closure = self.preferenceLoopClosure,
                reference_node = 0)

        global_optimization(self.poseGraph,
            GlobalOptimizationLevenbergMarquardt(),
            GlobalOptimizationConvergenceCriteria(), option)

        for point_id in range(len(self.pcDataset)):

            self.pcDataset[point_id].transform(self.poseGraph.nodes[point_id].pose)



    def generatePointClouds(self, radius=0.1, maxNN=30) :

        temp = []
        count = 1
        for i in self.rgbdDataset :

            pc = create_point_cloud_from_rgbd_image(i, self.intrinsics)
            estimate_normals(voxel_down_sample(pc, voxel_size=self.voxelSize), search_param=KDTreeSearchParamHybrid(radius=radius, max_nn=maxNN))
            temp.append(pc)
            count += 1

        return temp



    def loadRGBD(self, convert) :

        colorPath = os.path.join(self.datasetPath, "Color")
        depthPath = os.path.join(self.datasetPath, "Depth")

        colorFileList = sorted(os.listdir(colorPath), key = lambda x : int(x.split(".jpg")[0]))
        depthFileList = sorted(os.listdir(depthPath), key = lambda x : int(x.split(".png")[0]))

        if len(colorFileList) != len(depthFileList) :

            Logger.printError("Color and Depth directories do not contain the same amount of pictures !")
            exit()

        temp = []

        for a in range(self.minID, self.maxID) :

            colorImage = read_image(os.path.join(colorPath, colorFileList[a]))
            depthImage = read_image(os.path.join(depthPath, depthFileList[a]))
            rgbd = create_rgbd_image_from_color_and_depth(colorImage, depthImage, depth_trunc=self.maxDepth, convert_rgb_to_intensity=convert)

            temp.append(rgbd)

        return temp



    def waitForOrders(self) :

        while self.breakLoop == False :

            while self.controlQueue.qsize() == 0 :
                pass
            self.execOrder(self.controlQueue.get())



    def execOrder(self, order) :

        if order == "Break" :

            self.breakLoop = True

        if order == "Load Dataset" :

            Logger.printInfo("[Shard " + str(self.id) + "] Loading the RGBD dataset ...")
            self.rgbdDataset = self.loadRGBD(True)
            self.rgbdDatasetRGB = self.loadRGBD(False)
            Logger.printSuccess("[Shard " + str(self.id) + "] RGBD dataset (" + str(len(self.rgbdDataset)) + " images) successfully loaded !")

            self.intrinsics = read_pinhole_camera_intrinsic(self.intrinsicsPath)
            self.odometryOption = OdometryOption(min_depth=self.minDepth, max_depth=self.maxDepth, max_depth_diff=self.maxDepthDiff)


            self.sendDone()

        if order == "Generate Point Clouds" :

            Logger.printInfo("[Shard " + str(self.id) + "] Generating point clouds ...")
            self.pcDataset = self.generatePointClouds()
            Logger.printSuccess("[Shard " + str(self.id) + "] Point clouds (" + str(len(self.pcDataset)) + " point clouds) successfully generated !")

            self.sendDone()

        if order == "Generate Pose Graph" :

            Logger.printInfo("[Shard " + str(self.id) + "] Generating pose graph ...")
            self.registration()
            Logger.printSuccess("[Shard " + str(self.id) + "] Pose graph successfully generated !")

            self.sendDone()

        if order == "Pose Graph To Point Cloud" :

            Logger.printInfo("[Shard " + str(self.id) + "] Generating point cloud from pose graph ...")
            self.poseGraphToPointCloud()
            Logger.printSuccess("[Shard " + str(self.id) + "] Point cloud successfully generated !")

            self.sendDone()



    def sendDone(self) :

        self.answerQueue.put("Done")



    def __init__(self, minID, maxID, id, parameters, controlQueue, answerQueue) :

        set_verbosity_level(VerbosityLevel.Error)

        self.minID = minID
        self.maxID = maxID
        self.id = id
        self.controlQueue = controlQueue
        self.answerQueue = answerQueue

        self.name = parameters["name"]
        self.datasetPath = parameters["datasetPath"]
        self.intrinsicsPath = parameters["intrinsicsPath"]
        self.minDepth = parameters["minDepth"]
        self.maxDepth = parameters["maxDepth"]
        self.voxelSize = parameters["voxelSize"]
        self.maxDepthDiff = parameters["maxDepthDiff"]
        self.edgePruneThreshold = parameters["edgePruneThreshold"]
        self.preferenceLoopClosure = parameters["preferenceLoopClosure"]
        self.comparisonRange = parameters["comparisonRange"]
        self.voxelLength = parameters["voxelLength"]
        self.sdfTrunc = parameters["sdfTrunc"]
        self.volumeUnitResolution = parameters["volumeUnitResolution"]
        self.depthSamplingStride = parameters["depthSamplingStride"]

        self.rgbdDataset = []
        self.rgbdDatasetRGB = []
        self.pcDataset = []
        self.intrinsics = None
        self.breakLoop = False
        self.poseGraph = PoseGraph()

        self.sendDone()

        self.waitForOrders()
