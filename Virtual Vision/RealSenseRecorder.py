import time
import pyrealsense2 as rs2


class RealSenseRecorder(object):

    def record(self) :
        pass

    def close(self) :

        self.pipeline.stop()
    
    def __init__(self, scanDuration=0, fps=30, visualPreset=3, laserPower=240, exposure=3200, gain=16) :

        self.scanDuration = scanDuration
        self.fps = fps

        try :

            #Initialization
            self.pipeline = rs2.pipeline()
            self.config = rs2.config()

            #Enable streams
            self.config.enable_stream(rs2.stream.depth, 1280, 720, rs2.format.z16, self.fps)
            self.config.enable_stream(rs2.stream.color, 1280, 720, rs2.format.bgr8, self.fps)

            #Start streaming
            self.profile = self.pipeline.start(self.config)
            self.device = self.profile.get_device()
            self.depthSensor = self.device.first_depth_sensor()


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
            self.depthSensor.set_option(rs2.option.exposure, exposure)
            self.depthSensor.set_option(rs2.option.gain, gain)
            #self.depthSensor.set_option(rs2.option.max_distance, 4.0)


        except Exception as e :
            
            print("Unable to start the stream ...\n" + str(e))
            exit()

