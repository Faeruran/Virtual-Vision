import socket
import sys
import multiprocessing as mp
import json
import os
import time
import datetime
sys.path.append("../Utils/")
from Logger import Logger
sys.path.append("../Reconstruction")
import Reconstructor

class Socket :

    def connect(self) :

        Logger.printInfo("Binding socket on " + str(self.address) + ":" + str(self.port) + " ...")
        self.socket.bind((self.address, int(self.port)))
        Logger.printSuccess("Socket successfully bind on " + str(self.address) + ":" + str(self.port) + " !")
    

    def initConfigFile(self, connection) :

        #Ask for config file size
        connection.send("Config file size ?".encode("UTF-8"))
        #Receive config file size
        size = int(connection.recv(1024).decode("UTF-8"))
        #Send ACK for config file size
        connection.send("ACK CF Size".encode("UTF-8"))
        #Receive config file
        configFile = connection.recv(size).decode("UTF-8")
        Logger.printSuccess("Configuration file successfully received !")

        configFile = json.loads(str(configFile).replace("'", '"'))
        projectName = configFile["Name"]

        if not os.path.exists(os.path.join(self.workspaceDirectory, projectName)) :
            os.mkdir(os.path.join(self.workspaceDirectory, projectName))
        else :
            projectName = projectName + "-" + str(int(time.time()))
            os.mkdir(os.path.join(self.workspaceDirectory, projectName))
            configFile["Name"] = projectName
            
        
        projectDirectory = os.path.join(self.workspaceDirectory, projectName)

        configFile["Dataset Path"] = projectDirectory
        configFile["Intrinsics Path"] = os.path.join(projectDirectory, "Intrinsics.json")
                
        with open(os.path.join(projectDirectory, "rconfig.json"), "w") as jsonFile :
            json.dump(configFile, jsonFile, indent=4)

        datasetSize = int(configFile["Dataset Size"])

        #Send ACK for config file
        connection.send("ACK CF".encode("UTF-8"))

        return datasetSize, projectDirectory



    def initIntrinsicsFile(self, connection, projectDirectory) :

        #Receive intrinsics file size
        size = int(connection.recv(1024).decode("UTF-8"))
        #Send ACK for intrinsics file size
        connection.send("ACK IF Size".encode("UTF-8"))
        #Receive intrinsics file size
        intrinsicsFile = connection.recv(size).decode("UTF-8")
        Logger.printSuccess("Intrinsics file successfully received !")
        intrinsicsFile = json.loads(str(intrinsicsFile).replace("'", '"'))

        with open(os.path.join(projectDirectory, "Intrinsics.json"), "w") as jsonFile :
            json.dump(intrinsicsFile, jsonFile, indent=4)



    def initDataset(self, connection, datasetSize, projectDirectory) :

        depthPath = os.path.join(projectDirectory, "Depth")
        colorPath = os.path.join(projectDirectory, "Color")
                
        if not os.path.exists(depthPath) :
            os.mkdir(depthPath)

        if not os.path.exists(colorPath) :
            os.mkdir(colorPath)

        logCount = 0

        for i in range(datasetSize) :
            #Ask for a new image
            connection.send("New image ?".encode("UTF-8"))
            #Receive depth image size
            size = int(connection.recv(1024))
            #Send ACK for depth image size
            connection.send("ACK Depth Size".encode("UTF-8"))
            #Receive depth image
            depthImage = b""
            while len(depthImage) < size :
                temp = connection.recv(size - len(depthImage))
                if temp :
                    depthImage += temp

            with open(os.path.join(depthPath, str(i) + ".png"), "wb") as image :
                image.write(depthImage)
                logCount += 1
                progress = round(float(logCount) / (datasetSize * 2) * 100.0, 2)
                Logger.printProgress("Successfully receiving frame " + str(logCount) + "/" + str(datasetSize * 2) + " -> " + str(progress) + "%")

            #Send ACK for depth image
            connection.send("ACK Depth".encode("UTF-8"))
            #Receive color image size
            size = int(connection.recv(1024))
            #Send ACK for color image size
            connection.send("ACK Color Size".encode("UTF-8"))
            #Receive color image
            colorImage = b""
            while len(colorImage) < size :
                temp = connection.recv(size - len(colorImage))
                if temp :
                    colorImage += temp

            with open(os.path.join(colorPath, str(i) + ".jpg"), "wb") as image :
                image.write(colorImage)
                logCount += 1
                progress = round(float(logCount) / (datasetSize * 2) * 100.0, 2)
                Logger.printProgress("Successfully receiving frame " + str(logCount) + "/" + str(datasetSize * 2) + " -> " + str(progress) + "%")



    def getProjectsList(self) :

        temp = []

        for dir in os.listdir(self.workspaceDirectory) :

            print(os.path.join(*[self.workspaceDirectory, dir, "rconfig.json"]))

            if os.path.isfile(os.path.join(*[self.workspaceDirectory, dir, "rconfig.json"])) :
                temp.append(dir)

        return temp



    def newReconstruction(self, connection) :

        Logger.printInfo("Starting a new reconstruction !")

        datasetSize, projectDirectory = self.initConfigFile(connection)

        self.initIntrinsicsFile(connection, projectDirectory)
        
        self.initDataset(connection, datasetSize, projectDirectory)

        reconstructor = Reconstructor.Reconstructor(os.path.join(projectDirectory, "rconfig.json"), mergeOnly=False)

        connection.send("End".encode("UTF-8"))



    def mergeShards(self, connection) :

        connection.send("Dataset name ?".encode("UTF-8"))

        datasetName = connection.recv(1024).decode("UTF-8")

        projectsList = self.getProjectsList()
        print(projectsList)
        if datasetName in projectsList :
            connection.send("OK".encode("UTF-8"))
            reconstructor = Reconstructor.Reconstructor(os.path.join(*[self.workspaceDirectory, datasetName, "rconfig.json"]), mergeOnly=True)

        else :
            connection.send("KO".encode("UTF-8"))

        
    def listDatasets(self, connection) :
        
        datasetsList = self.getProjectsList()
        result = []

        for dataset in datasetsList :

            with open(os.path.join(*[self.workspaceDirectory, dataset, "rconfig.json"])) as file:

                    configFile = json.load(file)

                    shardFileList = os.listdir(configFile["Dataset Path"])
                    shardFileList = sorted([element for element in shardFileList if (".ply" in element and "Result" not in element)])

                    temp = {
                        "Name" : configFile["Name"],
                        "Date" : datetime.datetime.fromtimestamp(int(configFile["Date"])).strftime("%Y-%m-%d %H:%M:%S"),
                        "Size" : int(configFile["Dataset Size"]),
                        "Shard Size" : int(configFile["Shard Size"]),
                        "Number Of Shards" : len(shardFileList),
                        "Successfully Reconstructed" : True if "Result.ply" in os.listdir(configFile["Dataset Path"]) else False
                    }

                    result.append(temp)
        
        stringVersion = json.dumps(result)
        length = len(stringVersion)
        connection.send(str(length).encode("UTF-8"))
        data = connection.recv(1024).decode("UTF-8")

        if data == "ACK Size" :
            connection.send(stringVersion.encode("UTF-8"))



    def requestManager(self, connection, address) :

        data = ""

        while data != "Disconnect" :

            data = connection.recv(1024).decode("UTF-8")

            if data == "New Reconstruction" :

                self.newReconstruction(connection)

            elif data == "New Detection" :

                pass

            elif data == "Merge Shards" :

                self.mergeShards(connection)

            elif data == "List Datasets" :

                self.listDatasets(connection)

            elif data == "Remove Dataset" :

                pass
            
            elif data == "Get Result" :

                pass



    def run(self) :
        
        self.connect()

        self.socket.listen(5)
        Logger.printInfo("Socket waiting for connections ...")

        while True : 
  
            connection, address = self.socket.accept()
            Logger.printSuccess("Connection received from " + str(address) + "!")

            self.requestManager(connection, address)
            connection.close()

        Logger.printInfo("Closing connection with " + str(address) + " ...")
        self.socket.close()
        Logger.printSuccess("Connection with " + str(address) + " successfully closed !")



    def __init__(self, address, port, workspaceDirectory) :

        self.address = address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.workspaceDirectory = workspaceDirectory