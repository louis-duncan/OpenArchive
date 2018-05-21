import os
import time
import argparse

text_location = "bin\\temp\\message.dat"


def close():
    message_file = open(text_location, "w")
    message_file.write("exit")
    message_file.close()


if __name__ == "__main__":
    os.system("title OpenArchive")
    os.system("mode con: cols=35 lines=3")
    os.system("color F0")

    parser = argparse.ArgumentParser(description="Display message from file")
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
