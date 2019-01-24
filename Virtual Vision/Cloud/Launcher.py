import open3d
import argparse
import os
import sys
import json
sys.path.append("./Utils/")
from Logger import Logger
sys.path.append("./Reconstruction/")
import Reconstructor
import ShardAssembler
sys.path.append("./Socket/")
import Socket


def main() :
    
    os.system("clear")

    #workspaceDir = os.path.join(os.path.join(os.environ["HOME"]), "Workspace")
    workspaceDir = "/tmp/"

    parser = argparse.ArgumentParser(description="Virtual Vision v0.1 - Cloud")

    parser.add_argument("--address", action="store", nargs=1, default="192.168.100.156", type=str, required=True, help="Server's IP address")
    parser.add_argument("--port", action="store", nargs=1, default="55555", type=str, required=True, help="Server's port")
    parser.add_argument("--workspace", action="store", nargs=1, default=workspaceDir, type=str, required=False, help="Path of the workspace, where the datasets will be saved. Default : 'USER/Workspace'")

    args = parser.parse_args()

    parameters = {}
    parameters["Address"] = args.address[0] if not isinstance(type(args.address), str) else args.address
    parameters["Port"] = args.port[0] if not isinstance(type(args.port), str) else args.port
    parameters["Workspace"] = args.workspace
    
    sk = Socket.Socket(parameters["Address"], parameters["Port"], parameters["Workspace"])
    sk.run()

if __name__ == "__main__" :
    main()