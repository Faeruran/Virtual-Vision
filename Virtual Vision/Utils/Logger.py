import time
import sys
from termcolor import colored
from colorama import init, Style

class Logger(object):

    @staticmethod
    def printParameters(title, parameters) :

        init()
        print(Style.BRIGHT + colored(title + "\n", "red", "on_white"))
        for key, value in parameters.items() :

            toPrint = Style.BRIGHT + colored("\t[", "white") + Style.BRIGHT + colored(key, "green") + Style.BRIGHT + colored("] ---> ", "white") + Style.BRIGHT + colored(value, "blue")
            print(toPrint)

        print("\n")


    @staticmethod
    def printProgress(message) :

        init()
        now = time.localtime(time.time())

        timer = Style.BRIGHT + colored(str(now.tm_hour) + ":" + str(now.tm_min) + ":" + str(now.tm_sec), "red")
        header = Style.BRIGHT + colored("[PROGRESS]", "white", "on_yellow")
        message = Style.BRIGHT + colored(message, "yellow")

        print(timer + " " + header + " " + message)



    @staticmethod
    def printInfo(message) :

        init()
        now = time.localtime(time.time())

        timer = Style.BRIGHT + colored(str(now.tm_hour) + ":" + str(now.tm_min) + ":" + str(now.tm_sec), "red")
        header = Style.BRIGHT + colored("[INFO]", "white", "on_blue")
        message = Style.BRIGHT + colored(message, "blue")

        print(timer + " " + header + " " + message)

    @staticmethod
    def printUpdateInfo(message) :

        init()
        now = time.localtime(time.time())

        timer = Style.BRIGHT + colored(str(now.tm_hour) + ":" + str(now.tm_min) + ":" + str(now.tm_sec), "red")
        header = Style.BRIGHT + colored("[INFO]", "white", "on_blue")
        message = Style.BRIGHT + colored(message, "blue")

        sys.stdout.write("\r" + (timer + " " + header + " " + message))



    @staticmethod
    def printSuccess(message) :

        init()
        now = time.localtime(time.time())

        timer = Style.BRIGHT + colored(str(now.tm_hour) + ":" + str(now.tm_min) + ":" + str(now.tm_sec), "red")
        header = Style.BRIGHT + colored("[SUCCESS]", "white", "on_green")
        message = Style.BRIGHT + colored(message, "green")

        print(timer + " " + header + " " + message)




    @staticmethod
    def printError(message) :

        init()
        now = time.localtime(time.time())

        timer = Style.BRIGHT + colored(str(now.tm_hour) + ":" + str(now.tm_min) + ":" + str(now.tm_sec), "red")
        header = Style.BRIGHT + colored("[ERROR]", "white", "on_red")
        message = Style.BRIGHT + colored(message, "red")

        print(timer + " " + header + " " + message)



    @staticmethod
    def printAppTitle(message) :
        pass



    @staticmethod
    def printOperationTitle(message) :

        init()
        temp = Style.BRIGHT + colored("\n[#>>> ", "red", "on_white") + colored(message, "cyan", "on_white") + colored(" <<<#]\n", "red", "on_white")

        print(temp)



    @staticmethod
    def printSubOperationTitle(message) :

        init()
        print(Style.BRIGHT + colored(message + "\n", "red", "on_white"))
