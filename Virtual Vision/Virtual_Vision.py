import open3d
import argparse
import RealSenseRecorder
import atexit
import os


def main() :

    rootDir = os.path.join(os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop"), "Workspace")   

    parser = argparse.ArgumentParser(description="Virtual Vision v0.0")
    parser.add_argument("--scan", action="store", nargs=1, default=1, type=int, required=True, help="Record a new scan of the environment : 0/1")
    parser.add_argument("--nsec", action="store", nargs=1, default=0, type=int, required=False, help="Set the scan duration in seconds (0 for unlimited, press Q to quit)")
    parser.add_argument("--workspace", action="store", nargs=1, default=rootDir, type=str, required=False, help="Workspace directory, Desktop/Workspace by default")
    parser.add_argument("--sharpening", action="store", nargs=1, default=0, type=int, required=False, help="Sharpen blurry images : 0/1")
    args = parser.parse_args()
    print(args.sharpening[0])

    if args.scan[0] :
    
        rsr = RealSenseRecorder.RealSenseRecorder(scanDuration=args.nsec[0], fps=30, visualPreset=3, laserPower=240, exposure=3200, gain=16, rootDir=args.workspace, sharpening=bool(args.sharpening[0]))
        rsr.setupFolder()
        rsr.scan()
        
        atexit.register(rsr.close)


if __name__ == "__main__" :
    main()
