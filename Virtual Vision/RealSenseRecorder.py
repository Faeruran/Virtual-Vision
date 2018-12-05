import os
import time
import pyrealsense2 as rs2
import keyboard
import numpy as np
import cv2

class RealSenseRecorder(object):

    def imageSharpener(self, blurryImage) :

        #Sharpens a blurry image and returns it
        kernel = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
        return cv2.filter2D(blurryImage, -1, kernel)



    def setupFolder(self) :

        #Setup a new scan directory within the workspace (the name of the main directory will be the epoch time at the time of the creation)
        self.rootDir = os.path.join(self.rootDir, ("RSCapture-" + str(int(time.time()))))
        os.makedirs(self.rootDir)
        os.makedirs(os.path.join(self.rootDir, "Depth"))
        os.makedirs(os.path.join(self.rootDir, "Color"))



    def scan(self) :

        #Depending on the --nsec argument set by the user, this function will get, process and save the frames taken by the RealSense
        #This function will use a timer or just wait for the user to press Q
        #The depth images will be saved in a "Depth" directory, while the RGB frames will be saved within the "Color" directory
        #If sharpening is enabled, a sharpened copy of each RGB frame will be saved with the "-sharp" extension

        counter = 0

        if self.scanDuration :

            initTime = time.time()
            
            while time.time() - initTime < float(self.scanDuration) :

                depthFrame, colorFrame = self.getFrame()
                depthImage = np.asanyarray(depthFrame.data)
                colorImage = np.asanyarray(colorFrame.data)
                depthPath = os.path.join(os.path.join(self.rootDir, "Depth"), (str(counter) + ".png"))
                colorPath = os.path.join(os.path.join(self.rootDir, "Color"), (str(counter) + ".jpg"))

                cv2.imwrite(depthPath, depthImage)
                cv2.imwrite(colorPath, colorImage)

                if self.sharpening :

                    sharpColorPath = os.path.join(os.path.join(self.rootDir, "Color"), (str(counter) + "-sharp.jpg"))
                    #sharpDepthPath = os.path.join(os.path.join(self.rootDir, "Depth"), (str(counter) + "-sharp.png"))

                    cv2.imwrite(sharpColorPath, self.imageSharpener(colorImage))
                    #cv2.imwrite(sharpDepthPath, self.imageSharpener(depthImage))

                counter += 1



        else :

            while not keyboard.is_pressed("q") :

                depthFrame, colorFrame = self.getFrame()
                depthImage = np.asanyarray(depthFrame.data)
                colorImage = np.asanyarray(colorFrame.data)
                depthPath = os.path.join(os.path.join(self.rootDir, "Depth"), (str(counter) + ".png"))
                colorPath = os.path.join(os.path.join(self.rootDir, "Color"), (str(counter) + ".jpg"))

                cv2.imwrite(depthPath, depthImage)
                cv2.imwrite(colorPath, colorImage)

                if self.sharpening :

                    sharpColorPath = os.path.join(os.path.join(self.rootDir, "Color"), (str(counter) + "-sharp.jpg"))
                    #sharpDepthPath = os.path.join(os.path.join(self.rootDir, "Depth"), (str(counter) + "-sharp.png"))

                    cv2.imwrite(sharpColorPath, self.imageSharpener(colorImage))
                    #cv2.imwrite(sharpDepthPath, self.imageSharpener(depthImage))

                counter += 1

                time.sleep(0.1)


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
        self.depthSensor.stop()
        self.pipeline.stop()
        
        print("Pipeline closed")


    
    def __init__(self, scanDuration, rootDir, fps=30, visualPreset=3, laserPower=240, exposure=3200, gain=16, sharpening=False) :

        self.scanDuration = scanDuration
        self.fps = fps
        self.rootDir = rootDir
        self.sharpening = sharpening

        try :

            #Initialization
            self.pipeline = rs2.pipeline()
            self.config = rs2.config()
            #Enable streams
            self.config.enable_stream(rs2.stream.depth, 1280, 720, rs2.format.z16, self.fps)
            self.config.enable_stream(rs2.stream.color, 1280, 720, rs2.format.bgr8, self.fps)

            #Start streaming
            self.profile = self.pipeline.start(self.config)

        except Exception as e :
            
            print("Unable to start the stream ...\n" + str(e))
            exit()



        self.device = self.profile.get_device()
        self.depthSensor = self.device.first_depth_sensor()

        try :

            #Set parameters
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

            print("Unable to set one parameter on the RealSense. Gonna continue to run.\n" + str(e))
            pass

        #Create an align object -> aligning depth frames to color frames
        self.aligner = rs2.align(rs2.stream.color)


        

