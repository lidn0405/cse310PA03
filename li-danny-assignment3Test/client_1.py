'''
This module defines the behaviour of a client in your Chat Application
'''
import sys
import getopt
import socket
import random
from threading import Thread
import os
import util


'''
Write your code inside this class. 
In the start() function, you will read user-input and act accordingly.
receive_handler() function is running another thread and you have to listen 
for incoming messages in this function.
'''

class Client:
    '''
    This is the main Client Class. 
    '''
    def __init__(self, username, dest, port, window_size):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.name = username

    def handleMessage(self, message, server_addy):
        # Handle proper formatting
        try:
            num = int(message[1])
        except ValueError:
            print("incorrect userinput format")
            return 0

        numOfClients = int(message[1])
        # Actual message to be sent
        msg = " ".join(message[2+numOfClients:])
        # Make list into dict.fromkeys() to remove duplicates
        namesList = list(dict.fromkeys(message[2:2+numOfClients]))
        numOfClients = len(namesList)
        # Send only len and usernames and message at the end
        sendMessage = str(numOfClients) + " " + " ".join(namesList) + " " + msg
        # print(sendMessage)

        appMessage = util.make_message("send_message", 4, sendMessage)
        appPacket = util.make_packet("data", 0, appMessage)
        self.sock.sendto(appPacket.encode(), server_addy)
        return 0

    def hanldeList(self, message, server_addy):
        if len(message) > 1:
            print("incorrect userinput format")
            return 0

        message = util.make_message("request_users_list", 2)
        packet = util.make_packet("data", 0, message)

        self.sock.sendto(packet.encode(), server_addy)
        return 0

    def handleHelp(self, message, server_addy):
        print("msg <number_of_users> <username1> <username2> ... <message>")
        print("list")
        print("help")
        print("quit")
        return 0

    def handleQuit(self, message, server_addy):
        message = util.make_message("disconnect", 1, "")
        packet = util.make_packet("data", 0, message)

        self.sock.sendto(packet.encode(), server_addy)
        print("quitting")
        return -1

    def start(self):
        '''
        Main Loop is here
        Start by sending the server a JOIN message. 
        Use make_message() and make_util() functions from util.py to make your first join packet
        Waits for userinput and then process it
        '''
        # First join packet
        joinMsg = util.make_message("join", 1, self.name)
        joinPacket = util.make_packet("data", 0, joinMsg)

        server_addy = (self.server_addr, self.server_port)
        self.sock.sendto(joinPacket.encode(), server_addy)

        # While connected handle user requests
        while(True):
            userInp = input()
            # parse user input into an array
            messages = userInp.split(" ")
            cont = 0

            match messages[0]:
                case "msg":
                    cont = self.handleMessage(messages, server_addy)
                case "list":
                    cont = self.hanldeList(messages, server_addy)
                case "help":
                    cont = self.handleHelp(messages, server_addy)
                case "quit":
                    cont = self.handleQuit(messages, server_addy)
                case _:
                    print("incorrect userinput format")
                    continue
            
            # Break loop if quit
            if cont == -1:
                break

    connected = True

    def receive_handler(self):
        '''
        Waits for a message from server and process it accordingly
        '''
        while self.connected:
            data, addr = self.sock.recvfrom(1024)
            dataMsg = data.decode()
            msgArr = util.parse_packet(dataMsg)

            # Match the message type to handler
            res = msgArr[2].split(" ")
            match res[0]:
                case "err_server_full":
                    print("disconnected: server full")
                    self.sock.close()
                    self.connected = False
                    break
                case "err_username_unavailable":
                    print("disconnected: username not available")
                    self.sock.close()
                    self.connected = False
                    break
                case "response_users_list":
                    listMsg = "list:"
                    for names in res[2:]:
                        listMsg += " " + names
                    print(listMsg)
                case "forwarded_message":
                    sentMsg = "msg: " + res[2] + ":"
                    for words in res[3:]:
                        sentMsg += " " + words
                    print(sentMsg)
                case _:
                    print("disconnected: server received an unknown command")
    



# Do not change below part of code
if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our Client module completion
        '''
        print("Client")
        print("-u username | --user=username The username of Client")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW_SIZE | --window=WINDOW_SIZE The window_size, defaults to 3")
        print("-h | --help Print this help")
    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "u:p:a:w", ["user=", "port=", "address=","window="])
    except getopt.error:
        helper()
        exit(1)

    PORT = 15000
    DEST = "localhost"
    USER_NAME = None
    WINDOW_SIZE = 3
    for o, a in OPTS:
        if o in ("-u", "--user="):
            USER_NAME = a
        elif o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW_SIZE = a

    if USER_NAME is None:
        print("Missing Username.")
        helper()
        exit(1)

    S = Client(USER_NAME, DEST, PORT, WINDOW_SIZE)
    try:
        # Start receiving Messages
        T = Thread(target=S.receive_handler)
        T.daemon = True
        T.start()
        # Start Client
        S.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
