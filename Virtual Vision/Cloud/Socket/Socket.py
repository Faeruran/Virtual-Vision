import socket
import sys
import multiprocessing as mp
import json
import os
sys.path.append("../Utils/")
from Logger import Logger

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
                
        with open(os.path.join(self.projectDirectory, "rconfig.json"), "w") as jsonFile :
            json.dump(configFile, jsonFile, indent=4)

        datasetSize = int(configFile["Dataset Size"])

        #Send ACK for config file
        connection.send("ACK CF".encode("UTF-8"))

        return datasetSize



    def initIntrinsicsFile(self, connection) :

        #Receive intrinsics file size
        size = int(connection.recv(1024).decode("UTF-8"))
        #Send ACK for intrinsics file size
        connection.send("ACK IF Size".encode("UTF-8"))
        #Receive intrinsics file size
        intrinsicsFile = connection.recv(size).decode("UTF-8")
        Logger.printSuccess("Intrinsics file successfully received !")
        intrinsicsFile = json.loads(str(intrinsicsFile).replace("'", '"'))

        with open(os.path.join(self.projectDirectory, "Intrinsics.json"), "w") as jsonFile :
            json.dump(intrinsicsFile, jsonFile, indent=4)



    def initDataset(self, connection, datasetSize) :

        depthPath = os.path.join(self.projectDirectory, "Depth")
        colorPath = os.path.join(self.projectDirectory, "Color")
                
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



    def newReconstruction(self, connection) :

        Logger.printInfo("Starting a new reconstruction !")

        datasetSize = self.initConfigFile(connection)

        self.initIntrinsicsFile(connection)
        
        self.initDataset(connection, datasetSize)

        connection.send("End".encode("UTF-8"))

        

    def requestManager(self, connection, address) :

        data = ""

        while data != "Disconnect" :

            data = connection.recv(1024).decode("UTF-8")

            if data == "New Reconstruction" :

                self.newReconstruction(connection)

            if data == "New Detection" :

                pass



    def run(self) :
        
        self.connect()

        self.socket.listen(5)
        Logger.printInfo("Socket waiting for connections ...")

        while True : 
  
            connection, address = self.socket.accept()
            Logger.printSuccess("Connection received from " + str(address) + "!")

            self.requestManager(connection, address)

        Logger.printInfo("Closing connection with " + str(address) + " ...")
        self.socket.close()
        Logger.printSuccess("Connection with " + str(address) + " successfully closed !")



    def __init__(self, address, port, projectDirectory) :

        self.address = address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.projectDirectory = projectDirectory