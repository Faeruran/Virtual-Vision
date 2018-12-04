import open3d
import argparse
import RealSenseRecorder


def main() :

    parser = argparse.ArgumentParser(description="Virtual Vision v0.0")
    parser.add_argument("--scan", action="store", nargs=1, default=True, type=bool, required=True, help="Record a new scan of the environment : True/False")
    parser.add_argument("--nsec", action="store", nargs=1, default=0, type=int, required=False, help="Set the scan duration in seconds (0 for unlimited, press Q to quit)")
    args = parser.parse_args()

    rsr = RealSenseRecorder.RealSenseRecorder()


if __name__ == "__main__" :
    main()
