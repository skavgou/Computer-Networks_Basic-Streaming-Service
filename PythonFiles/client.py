# based on https://pythontic.com/modules/socket/udp-client-server-example
import socket
import sys
import select
import cv2, pickle, numpy as np, os
import time
import matplotlib.pyplot as plt
import threading
from threading import Thread

blank = (int("0000", 2))
blank = blank.to_bytes(1, 'big')

myStreams = []

def send(type):

    idByte = (int("0000",2))
    idByte = idByte.to_bytes(1,'big')

    if type[:3] == 'msg':
        typeByte = (int("0001", 2))
        typeByte = typeByte.to_bytes(1, 'big')
        dummyBits = (int("000000000001", 2))
        dummyBits = dummyBits.to_bytes(3, 'big')
        data = str.encode(msgFromClient)
        bytesToSend = idByte + typeByte + dummyBits + blank + data
        print("sending")
        UDPClientSocket.sendto(bytesToSend, brokerAddressPort)
    elif type[:3] == 'req':
        streamID = type[4:len(type)]
        typeByte = int("0010", 2)
        typeByte = typeByte.to_bytes(1, 'big')
        streamID = int(streamID, 2)
        streamID = streamID.to_bytes(3,'big')
        data = str.encode("Sponge he's one tap, do not fumble this")
        bytesToSend = idByte + typeByte + streamID + blank + data
        UDPClientSocket.sendto(bytesToSend, brokerAddressPort)
        stream = []
        stream.append(streamID)
        stream.append(-1)
        myStreams.append(stream)
    elif type[:3] == 'uns':
        streamID = type[4:len(type)]
        typeByte = int("0011", 2)
        typeByte = typeByte.to_bytes(1, 'big')
        streamID = int(streamID, 2)
        streamID = streamID.to_bytes(3, 'big')
        data = str.encode("I'm trying Squid!")
        bytesToSend = idByte + typeByte + streamID + blank + data
        UDPClientSocket.sendto(bytesToSend, brokerAddressPort)
        for i in myStreams:
            if streamID == i[0]:
                myStreams.remove(i)

def decodeAudio(data):
    data = np.frombuffer(data)
    plt.figure(figsize=(16, 10))
    plt.plot(data)
    plt.title("Sample MP3 loading into Numpy")
    plt.show()

def printID(header):
    id = header[2:4]
    idString = ""
    for i in id:
        binaryRep = bin(i)
        binaryRep = binaryRep[2:].zfill(8)
        idString += binaryRep
    return idString


def listen():
    bytesAddressPair = UDPClientSocket.recvfrom(bufferSize)
    sentInfo = bytesAddressPair[0]
    address = bytesAddressPair[1]
    header = sentInfo[:7]
    data = sentInfo[7:len(sentInfo)]
    if header[0] == 2:
        #start = time.perf_counter()
        #print("Verified data is from broker.")
        if header[1] == 5:
            print(data.decode())
        for i in myStreams:
            #print("Checking streams")
            if header[2:5] == i[0]:
                #print("Stream found")
                if int.from_bytes(header[5:7],'big') >= i[1] or i[1] == -1 or header[5] == 0:
                    #startTime = time.perf_counter()
                    #print("Receiving frame " + str(header[5]))
                    if header[1] == 3:
                        #print("Received message from streamer: " + printID(header))
                        print(data.decode())
                    if header[1] == 1:
                        decodeVideo(data)
                        #thread = threading.Thread(target=decodeVideo, args=(data,))
                        #thread.start()
                    elif header[1] == 2:
                        print(data.decode())
                    elif header[1] == 0:
                        decodeImage(data)
                    elif header[1] == 4:
                        decodeAudio(data)
                    #clockTime = time.perf_counter() - startTime
                    #print("Ran conditional, " + str(clockTime))
                    i[1] += 1
        #clockTime = time.perf_counter() - start
        #print("overall, " + str(clockTime))



def decodeVideo(videoData):
    startTime = time.perf_counter()
    data = pickle.loads(videoData)  # All byte code is converted to Numpy Code
    data = cv2.imdecode(data, cv2.IMREAD_COLOR)
    #print(data)
    cv2.imshow('Sent Video', data)  # Show Video/Stream
    clockTime = time.perf_counter() - startTime
    print("video decoded, " + str(clockTime))

def decodeImage(videoData):
    data = pickle.loads(videoData)  # All byte code is converted to Numpy Code
    data = cv2.imdecode(data, cv2.IMREAD_COLOR)
    #print(data)
    cv2.imshow('Sent Image', data)  # Show Video/Stream

rlistRes = [[]]
readableRes = [[]]




print("Client start!")

localIP     = "client"

msgFromClient       = "Hello UDP Broker"

brokerAddressPort   = ("broker", 50002)
bufferSize          = 524288000

# Create a UDP socket at client side
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

run = True

ClientSock = [UDPClientSocket]

rlistArr = [[]]
readableArr = [[]]

def scanForText():
    rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
    rlistArr[0] = rlist

def scanForPorts():
    readable, _, _ = select.select(ClientSock, [], [], 0.01)
    readableArr[0] = readable



while run:

    # Check if there's data to read from sys.stdin (standard input)
    thread1 = threading.Thread(target=scanForText(), args=())
    thread2 = threading.Thread(target=scanForPorts(), args=())
    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()


    if rlistArr[0]:
        user_input = sys.stdin.readline().strip()
        #print(f"User input: {user_input}")
        send(user_input)



    # Check for incoming packets


    for s in readableArr[0]:
        if s is UDPClientSocket:
            #data, addr = UDPClientSocket.recvfrom(5000000)
            start = time.perf_counter()
            listen()

    if cv2.waitKey(1) == 13:
        cv2.destroyAllWindows()


