import os
import time
import argparse

os.system("title OpenArchive")
os.system("mode con: cols=35 lines=3")
os.system("color F0")

text_location = "bin\\temp\\message.dat"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deiplay message from file")
    parser.add_argument("-m", "--message", default="Loading...")
    args = vars(parser.parse_args())

    file = open(text_location, "w")
    file.write(args["message"])
    file.close()

    while True:
        if os.path.exists(text_location):
            os.system("cls")
            file = open(text_location)
            text = file.read()
            file.close()
            if text == "exit":
                os.remove(text_location)
                break
            print(text)
            time.sleep(0.5)
        else:
            break
