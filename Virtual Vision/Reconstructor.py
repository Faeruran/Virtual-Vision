import open3d
import json
from Logger import Logger

class Reconstructor(object) :

    def loadRGBD(self, workspace) :

        temp = []
        return temp



    def loadParams(self, paramFile) :

        try :

            with open(paramFile) as file:

                    paramDict = json.load(file)
                    Logger.printSuccess("Reconstruction parameters successfully loaded !")
                    Logger.printParameters("RECONSTRUCTION PARAMETERS", paramDict)

                    for key, value in paramDict.items() :

                        self.name = value if key == "Name" else self.name
                        self.datasetPath = value if key == "Dataset Path" else self.datasetPath
                        self.intrinsicsPath = value if key == "Intrinsics Path" else self.intrinsicsPath
                        self.fragmentSize = value if key == "Fragment Size" else self.fragmentSize
                        self.minDepth = value if key == "Min Depth" else self.minDepth
                        self.maxDepth = value if key == "Max Depth" else self.maxDepth
                        self.voxelSize = value if key == "Voxel Size" else self.voxelSize

        except Exception as e:

            Logger.printError("Could not read the reconstruction parameters file"))
            exit()



    def __init__(self, paramFile) :

        self.name = None
        self.datasetPath = None
        self.intrinsicsPath = None
        self.fragmentSize = None
        self.minDepth = None
        self.maxDepth = None
        self.voxelSize = None

        Logger.printInfo("Loading the reconstruction parameter file ...")
        self.loadParams(paramFile.replace('"', ''))



        #self.rgbdDataset = self.loadRGBD()
