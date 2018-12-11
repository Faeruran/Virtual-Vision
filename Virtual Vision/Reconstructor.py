from open3d import *
import os
import json
import numpy as np
from Logger import Logger

class Reconstructor(object) :





    def loadRGBD(self) :

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

            temp.append(create_rgbd_image_from_color_and_depth(colorImage, depthImage))

        Logger.printSuccess("RGBD dataset (" + str(len(colorFileList * 2)) + " images) successfully loaded !")

        return temp



    def loadParams(self, paramFile) :

        try :

            with open(paramFile) as file:

                    paramDict = json.load(file)


                    for key, value in paramDict.items() :

                        self.name = value if key == "Name" else self.name
                        self.datasetPath = value if key == "Dataset Path" else self.datasetPath
                        self.intrinsicsPath = value if key == "Intrinsics Path" else self.intrinsicsPath
                        self.fragmentSize = value if key == "Fragment Size" else self.fragmentSize
                        self.minDepth = value if key == "Min Depth" else self.minDepth
                        self.maxDepth = value if key == "Max Depth" else self.maxDepth
                        self.voxelSize = value if key == "Voxel Size" else self.voxelSize

                    Logger.printSuccess("Reconstruction parameters successfully loaded !\n")
                    Logger.printParameters("RECONSTRUCTION PARAMETERS", paramDict)

        except Exception as e:

            Logger.printError("Could not read the reconstruction parameters file")
            exit()



    def __init__(self, paramFile) :

        #Parameters
        self.name = None
        self.datasetPath = None
        self.intrinsicsPath = None
        self.fragmentSize = None
        self.minDepth = None
        self.maxDepth = None
        self.voxelSize = None

        Logger.printInfo("Loading the reconstruction parameter file ...")
        self.loadParams(paramFile.replace('"', ''))

        #Data variables
        Logger.printInfo("Loading the images ...")
        self.rgbdDataset = self.loadRGBD()
        #print(self.rgbdDataset)



        #self.rgbdDataset = self.loadRGBD()
