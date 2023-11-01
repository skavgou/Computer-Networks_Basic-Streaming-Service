# based on https://pythontic.com/modules/socket/udp-client-server-example
import socket
import sys
import select
import cv2, pickle, numpy as np, os
import time
import matplotlib.pyplot as plt
import threading
from pydub import AudioSegment
import io
from threading import Thread

blank = (int("0000", 2))
blank = blank.to_bytes(1, 'big')

dcByte = (int("0110", 2))
dcByte = dcByte.to_bytes(1, 'big')

msgByte = (int("0001", 2))
msgByte = msgByte.to_bytes(1, 'big')

reqByte = (int("0010", 2))
reqByte = reqByte.to_bytes(1, 'big')

unsByte = (int("0011", 2))
unsByte = unsByte.to_bytes(1, 'big')

blankStream = (int("000000000001", 2))
blankStream = blankStream.to_bytes(3, 'big')

myStreams = []

def send(type):

    idByte = (int("0000",2))
    idByte = idByte.to_bytes(1,'big')

    complete = False

    while not complete:

        if type[:3] == 'msg':
            data = str.encode(msgFromClient)
            bytesToSend = idByte + msgByte + blankStream + data
            print("Sending request for stream list")
            UDPClientSocket.sendto(bytesToSend, brokerAddressPort)
        elif type[:3] == 'req':
            streamID = type[4:len(type)]
            streamID = bytes.fromhex(streamID)
            data = str.encode("Connect request")
            bytesToSend = idByte + reqByte + streamID + data
            UDPClientSocket.sendto(bytesToSend, brokerAddressPort)
            stream = []
            stream.append(streamID)
            stream.append(-1)
            myStreams.append(stream)
        elif type[:3] == 'uns':
            streamID = type[4:len(type)]
            streamID = bytes.fromhex(streamID)
            data = str.encode("Unsubscribe request")
            bytesToSend = idByte + unsByte + streamID + data
            UDPClientSocket.sendto(bytesToSend, brokerAddressPort)
            for i in myStreams:
                if streamID == i[0]:
                    myStreams.remove(i)
        elif type[:10] == "disconnect":
            toSend = idByte + dcByte + blankStream + str.encode("Dc request")
            UDPClientSocket.sendto(toSend, brokerAddressPort)

        print("Waiting for acknowledgement from Broker...")
        for i in range(30):
            bytesAddressPair = UDPClientSocket.recvfrom(bufferSize)
            sentInfo = bytesAddressPair[0]
            print(sentInfo[1])
            if sentInfo[1] == 15:
                complete = True
                listen(sentInfo)
            else:
                listen(sentInfo)

            if complete:
                break



def decodeAudio(data):
    audio_segment = AudioSegment.from_mp3(io.BytesIO(data))
    # Save the MP3 file
    audio_segment.export("output.mp3", format="mp3")

def printID(header):
    id = header[2:4]
    idString = ""
    for i in id:
        binaryRep = bin(i)
        binaryRep = binaryRep[2:].zfill(8)
        idString += binaryRep
    return idString


def listen(sentInfo):
    header = sentInfo[:8]
    data = sentInfo[8:len(sentInfo)]
    if header[0] == 2:
        if header[1] == 5 or header[1] == 15:
            print(data.decode())
        for i in myStreams:
            if header[2:6] == i[0]:
                if int.from_bytes(header[5:8],'big') >= i[1] or i[1] == -1 or header[5] == 0:
                    if header[1] == 3:
                        print(data.decode())
                    if header[1] == 1:
                        decodeVideo(header, data)
                    elif header[1] == 2:
                        print(data.decode())
                    elif header[1] == 0:
                        decodeImage(data)
                    elif header[1] == 4:
                        decodeAudio(data)
                    i[1] = int.from_bytes(header[5:8],'big')



def decodeVideo(header, videoData):
    data = pickle.loads(videoData)  # All byte code is converted to Numpy Code
    data = cv2.imdecode(data, cv2.IMREAD_COLOR)
    #print(data)
    cv2.imshow('Sent Video:' + str(header[2:6]), data)  # Show Video/Stream

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
bufferSize          = 5242880

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
            bytesAddressPair = UDPClientSocket.recvfrom(bufferSize)
            sentInfo = bytesAddressPair[0]
            listen(sentInfo)

    if cv2.waitKey(1) == 13:
        cv2.destroyAllWindows()


