'''
This module defines the behaviour of server in your Chat Application
'''
import sys
import getopt
import socket
import util


class Server:
    '''
    This is the main Server Class. You will  write Server code inside this class.
    '''
    def __init__(self, dest, port, window):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)
        self.sock.bind((self.server_addr, self.server_port))

    # name: addr
    clients = {}

    # Handling functions for each request from client
    def handleJoin(self, addr, messages):
        if len(self.clients) >= util.MAX_NUM_CLIENTS:
            print("disconnected: server full")
            res = util.make_message("err_server_full", 2)
            packet = util.make_packet("data", 0, res)
            self.sock.sendto(packet.encode(), addr)
            return
        
        if messages[2] in self.clients:
            print("disconnected: username not available")
            res = util.make_message("err_username_unavailable", 2)
            packet = util.make_packet("data", 0, res)
            self.sock.sendto(packet.encode(), addr)
            return
        
        self.clients[messages[2]] = addr
        print(f"join: {messages[2]}")
        return

    def handleReqUserList(self, addr, messages):
        names = list(self.clients.keys())
        names.sort()
        nameString = " ".join(names)

        res = util.make_message("response_users_list", 3, nameString)
        packet = util.make_packet("data", 0, res)
        self.sock.sendto(packet.encode(), addr)
        name = self.getNameFromAddress(addr)
        print(f"request_users_list: {name}")
        return

    def getNameFromAddress(self, addr):
        for name in list(self.clients.keys()):
            if self.clients[name] == addr:
                return name
        
        return -1

    # Duplicates are already removed
    def handleSendMsg(self, addr, messages):
        senderUser = self.getNameFromAddress(addr)
        print(f"msg: {senderUser}")

        # Recipients to message
        recipients = messages[3 : int(messages[2]) + 3]
        # Actual message
        msg = " ".join(messages[3 + int(messages[2]):])
        # print(f"MESSAGE: {msg}")

        for name in recipients:
            if name not in self.clients.keys():
                print(f"msg: {senderUser} to non-existent user {name}")
            else:
                # print(f"NAME: {name}")
                message = senderUser + " " + msg
                # print(f"FULL MESSAGE: {message}")
                forward = util.make_message("forwarded_message", 4, message)
                forwardPacket = util.make_packet("data", 0, forward)
                self.sock.sendto(forwardPacket.encode(), self.clients[name])

        return
        

    def handleDisconnect(self, addr, messages):
        name = self.getNameFromAddress(addr)
        if name in self.clients:
            del self.clients[name]
            print(f"disconnected: {name}")
            print(self.clients)
        else:
            print("Error: no address found")

    # Directs to handler functions
    def handleData(self, addr, msgArr):
        # Parses data (msgArr[2]) into type, length, ...
        messages = msgArr[2].split(" ")
        # Sends message array into functions
        match messages[0]:
            case "join":
                return self.handleJoin(addr, messages)
            case "request_users_list":
                return self.handleReqUserList(addr, messages)
            case "send_message":
                return self.handleSendMsg(addr, messages)
            case "disconnect":
                return self.handleDisconnect(addr, messages)
            case _:
                name = self.getNameFromAddress(addr)
                if name not in self.clients:
                    print("no user found")
                else:
                    print(f"disconnected: {name} sent unknown command")
                res = util.make_message("err_unknown_message", 2)
                resPacket = util.make_packet("data", 0, res)
                self.sock.sendto(resPacket.encode(), addr)
                return


    def start(self):
        '''
        Main loop.
        continue receiving messages from Clients and processing it.
        
        '''
        while True:
            data, addr = self.sock.recvfrom(1024)
            dataMsg = data.decode()
            msgArr = util.parse_packet(dataMsg)

            res = self.handleData(addr, msgArr)
            

# Do not change below part of code

if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our module completion
        '''
        print("Server")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW | --window=WINDOW The window size, default is 3")
        print("-h | --help Print this help")

    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "p:a:w", ["port=", "address=","window="])
    except getopt.GetoptError:
        helper()
        exit()

    PORT = 15000
    DEST = "localhost"
    WINDOW = 3

    for o, a in OPTS:
        if o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW = a

    SERVER = Server(DEST, PORT,WINDOW)
    try:
        SERVER.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
