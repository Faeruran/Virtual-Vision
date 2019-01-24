from open3d import *
import ShardProcessor
import ShardAssembler
import os
import json
import numpy as np
import copy
import opencv_pose_estimation as ope
import sys
import time
from copy import deepcopy
from math import ceil
import multiprocessing as mp
sys.path.append("../Utils/")
from Logger import Logger



class Reconstructor(object) :

    def loadParams(self, paramFile) :

        try :

            with open(paramFile) as file:

                    paramDict = json.load(file)
                    parameters = {
                        "name" : None,
                        "datasetPath" : None,
                        "intrinsicsPath" : None,
                        "shardSize" : None,
                        "minDepth" : None,
                        "maxDepth" : None,
                        "voxelSize" : None,
                        "maxDepthDiff" : None,
                        "edgePruneThreshold" : None,
                        "preferenceLoopClosure" : None,
                        "comparisonRange" : None,
                        "voxelLength" : None,
                        "sdfTrunc" : None,
                        "volumeUnitResolution" : None,
                        "depthSamplingStride" : None,
                        "correspondenceRatio" : None,
                        "maxIterations" : None,
                        "maxValidation" : None,
                        "relativeFitness" : None,
                        "relativeRMSE" : None
                    }

                    for key, value in paramDict.items() :

                        parameters["name"] = value if key == "Name" else parameters["name"]
                        parameters["datasetPath"] = value if key == "Dataset Path" else parameters["datasetPath"]
                        parameters["intrinsicsPath"] = value if key == "Intrinsics Path" else parameters["intrinsicsPath"]
                        parameters["shardSize"] = int(value) if key == "Shard Size" else parameters["shardSize"]
                        parameters["minDepth"] = float(value) if key == "Min Depth" else parameters["minDepth"]
                        parameters["maxDepth"] = float(value) if key == "Max Depth" else parameters["maxDepth"]
                        parameters["voxelSize"] = float(value) if key == "Voxel Size" else parameters["voxelSize"]
                        parameters["maxDepthDiff"] = float(value) if key == "Max Depth Difference" else parameters["maxDepthDiff"]
                        parameters["edgePruneThreshold"] = float(value) if key == "Edge Prune Threshold" else parameters["edgePruneThreshold"]
                        parameters["preferenceLoopClosure"] = float(value) if key == "Preference Loop Closure" else parameters["preferenceLoopClosure"]
                        parameters["comparisonRange"] = int(value) if key == "Comparison Range" else parameters["comparisonRange"]
                        parameters["voxelLength"] = float(value) if key == "Voxel Length" else parameters["voxelLength"]
                        parameters["sdfTrunc"] = float(value) if key == "SDF Trunc" else parameters["sdfTrunc"]
                        parameters["volumeUnitResolution"] = int(value) if key == "Volume Unit Resolution" else parameters["volumeUnitResolution"]
                        parameters["depthSamplingStride"] = int(value) if key == "Depth Sampling Stride" else parameters["depthSamplingStride"]
                        parameters["correspondenceRatio"] = float(value) if key == "Correspondence Ratio" else parameters["correspondenceRatio"]
                        parameters["maxIterations"] = int(value) if key == "Max Iterations" else parameters["maxIterations"]
                        parameters["maxValidation"] = int(value) if key == "Max Validation" else parameters["maxValidation"]
                        parameters["relativeFitness"] = float(value) if key == "Relative Fitness" else parameters["relativeFitness"]
                        parameters["relativeRMSE"] = float(value) if key == "Relative RMSE" else parameters["relativeRMSE"]

                    Logger.printSuccess("Reconstruction parameters successfully loaded !\n")
                    Logger.printParameters("RECONSTRUCTION PARAMETERS", paramDict)

                    return parameters

        except Exception as e:

            Logger.printError("Could not read the reconstruction parameters file")
            print(e)
            exit()



    def getDatasetLength(self) :

        colorPath = os.path.join(self.parameters["datasetPath"], "Color")
        depthPath = os.path.join(self.parameters["datasetPath"], "Depth")

        colorFolderSize = len(os.listdir(colorPath))
        depthFolderSize = len(os.listdir(depthPath))

        if colorFolderSize != depthFolderSize :

            Logger.printError("Color and Depth directories do not contain the same amount of pictures !")
            exit()

        return colorFolderSize



    def initProcesses(self, num, poolSize) :

        for i in range(0, poolSize) :

            self.controlQueues.append(mp.Queue())
            self.answerQueues.append(mp.Queue())

        for i in range(0, poolSize) :

            if (((self.numCPU * num) + i) + 1) * self.shardSize <= self.datasetLength :
                self.processList.append(mp.Process(target=ShardProcessor.ShardProcessor, args=(self.shardSize * ((self.numCPU * num) + i), self.shardSize * (((self.numCPU * num) + i) + 1), ((self.numCPU * num) + i), self.parameters, self.controlQueues[((self.numCPU * num) + i)], self.answerQueues[((self.numCPU * num) + i)],)))
                self.processList[((self.numCPU * num) + i)].start()
                Logger.printInfo("Shard processor " + str(((self.numCPU * num) + i)) + " launched !")
                self.datasetSizes.append(self.shardSize * ((self.numCPU * num) + i))

            else :
                self.processList.append(mp.Process(target=ShardProcessor.ShardProcessor, args=(self.shardSize * ((self.numCPU * num) + i), (self.shardSize * ((self.numCPU * num) + i) + (self.datasetLength % self.shardSize)), ((self.numCPU * num) + i), self.parameters, self.controlQueues[((self.numCPU * num) + i)], self.answerQueues[((self.numCPU * num) + i)],)))
                self.processList[((self.numCPU * num) + i)].start()
                Logger.printInfo("Shard processor " + str(((self.numCPU * num) + i)) + " launched !")
                self.datasetSizes.append(self.shardSize * ((self.numCPU * num) + i))



    def sendOrder(self, order, num, poolSize) :

        for i in range(0, poolSize) :

            self.controlQueues[(self.numCPU * num) + i].put(order)



    def joinProcesses(self, num, poolSize) :

        for i in range(0, poolSize) :

            self.processList[(self.numCPU * num) + i].join()



    def checkIfDone(self, num, poolSize) :

        done = True
        messages = []

        for i in range(0, poolSize) :

            if self.answerQueues[(self.numCPU * num) + i].qsize() == 0 :

                return False

        for j in range(0, poolSize) :

            messages.append(self.answerQueues[(self.numCPU * num) + j].get())

        done = (messages[1:] == messages[:-1]) and (messages[0] == "Done")

        if done :

            return done

        else :

            for k in range(0, poolSize) :

                self.answerQueues[(self.numCPU * num) + k].put(messages[(self.numCPU * num) + k])

            return done



    def createShards(self) :

        Logger.printSubOperationTitle("CREATING SHARDS")

        numOperations = float(self.numShards) / self.numCPU

        if numOperations % 1.0 != 0 :

            numOperations += 1

        for i in range(0, int(numOperations)) :

            poolSize = self.numShards / ((i + 1) * self.numCPU)

            if poolSize < 1 :
                poolSize = self.numShards % self.numCPU
            else :
                poolSize = self.numCPU

            self.initProcesses(i, poolSize)
            while not self.checkIfDone(i, poolSize) :
                pass
            print("\n")

            self.sendOrder("Load Dataset", i, poolSize)
            while not self.checkIfDone(i, poolSize) :
                pass
            print("\n")

            self.sendOrder("Generate Point Clouds", i, poolSize)
            while not self.checkIfDone(i, poolSize) :
                pass
            print("\n")

            self.sendOrder("Generate Pose Graph", i, poolSize)
            while not self.checkIfDone(i, poolSize) :
                pass
            print("\n")

            self.sendOrder("Pose Graph To Point Cloud", i, poolSize)
            while not self.checkIfDone(i, poolSize) :
                pass
            print("\n")

            self.sendOrder("Break", i, poolSize)
            self.joinProcesses(i, poolSize)



    def importShards(self) :

        shardFileList = os.listdir(self.parameters["datasetPath"])
        shardFileList = sorted([element for element in shardFileList if ".ply" in element])

        for shardFile in shardFileList :

            self.shards.append(read_point_cloud(os.path.join(self.parameters["datasetPath"], shardFile)))



    def __init__(self, paramFile) :

        set_verbosity_level(VerbosityLevel.Error)

        Logger.printInfo("Loading the reconstruction parameter file ...")
        self.parameters = self.loadParams(paramFile.replace('"', ''))
        self.datasetLength = self.getDatasetLength()
        Logger.printInfo("Dataset size : " + str(self.datasetLength))

        self.numCPU = mp.cpu_count() - 1
        self.shardSize = int(self.parameters["shardSize"])
        if self.numCPU * (self.shardSize - 1) > self.datasetLength :

            Logger.printError("Incorrect shard size !")
            self.shardSize = int(self.datasetLength / self.numCPU)
            Logger.printInfo("Shard size set to " + str(self.shardSize))


        self.numShards = ceil(float(self.datasetLength / self.shardSize))
        Logger.printInfo("Number of shards : " + str(self.numShards))
        self.datasetSizes = []

        self.processList = []
        self.controlQueues = []
        self.answerQueues = []

        self.createShards()

        self.shards = []
        self.importShards()
        self.assembler = ShardAssembler.ShardAssembler(self.parameters, self.shards, self.datasetSizes)
