
import socket
import sys
import select
import cv2, numpy, pickle, os
import keyboard

blank = (int("0000", 2))
blank = blank.to_bytes(1, 'big')

def decodeMessage(messageData):
    data = messageData.decode()
    receivedMsg = "Message from sender:{}".format(data)
    print(receivedMsg)

#def decodeVideo(videoData):
#    data = pickle.loads(videoData)  # All byte code is converted to Numpy Code
#    data = cv2.imdecode(data, cv2.IMREAD_COLOR)
#    print(data)
#    cv2.imshow('sent vid', data)  # Show Video/Stream


def addToOldSubscription(header, client):
    for i in client[1]:
        if i == header[2:5]:
            print('Already subscribed')
            msg = "You are already subscribed to that stream"
            return
    client[1].append(header[2:5])


def addSubscription(header, client):
    client[1].append(header[2:5])
    print("Client subscribed")

def subscribeClient(header, data, port):
    oldClient = False
    for i in clients:
        if i[0] == port:
            oldClient = True
            addToOldSubscription(header, i)

    if oldClient == False:
        newClient = []
        newClient.append(port)
        newClient.append([])
        if header[1] == 1:
            decodeMessage(data)
        elif header[1] == 2:
            addSubscription(header, newClient)
        clients.append(newClient)

def sendServerList(header,data,port):
    msg = ""

    if not servers:
        msg = "We have no active streams right now :("
    else:
        msg += "Streams: Note some streams may not be currently running\n"
        for i in servers:
            for j in i[1]:
                for k in j[0]:
                    binaryRep = bin(k)
                    binaryRep = binaryRep[2:].zfill(8)
                    msg += binaryRep
                msg += " - " + j[1] + "\n"


    data = str.encode(msg)

    idByte = (int("0010", 2))
    idByte = idByte.to_bytes(1, 'big')

    typeByte = (int("0101", 2))
    typeByte = typeByte.to_bytes(1, 'big')

    dummyBits = int("000000000000", 2)
    dummyBits = dummyBits.to_bytes(3, 'big')


    header = idByte + typeByte + dummyBits + blank
    bytesToSend = header + data

    #print("Send it")

    UDPBrokerSocket.sendto(bytesToSend, port)

def unsubServer(header, port):
    for i in clients:
        if i[0] == port:
            if header[2:5] in i[1]:
                i[1].remove(header[2:5])

def handleClient(sentInfo, port):
    print("Handling client")
    header = sentInfo[:6]
    data   = sentInfo[6:len(sentInfo)]

    if header[1] == 2:
        subscribeClient(header, data, port)
    elif header[1] == 1:
        print("Sending server list")
        sendServerList(header,data,port)
    elif header[1] == 3:
        unsubServer(header,port)




def sendVideo(header, data):
    idByte = (int("0010", 2))
    idByte = idByte.to_bytes(1, 'big')

    typeByte = (int("0001", 2))
    typeByte = typeByte.to_bytes(1, 'big')

    streamBytes  = header[2:7]
    newHeader   = idByte + typeByte + streamBytes

    for i in clients:
        for j in i[1]:
            if j == header[2:5]:
                print("sending frame " + str(header[5]))
                bytesToSend = newHeader + data
                UDPBrokerSocket.sendto(bytesToSend, i[0])




def processVideo(sentInfo, address):
    header = sentInfo[:7]
    data = sentInfo[7:len(sentInfo)]
    oldStream = False
    oldStreamer = False
    oldStreamerID = 0
    for i in servers:
        if i[0] == header[2:4]:
            oldStreamer = True
            oldStreamerID = i
            for j in i[1]:
                if j[0] == header[2:5]:
                    oldStream = True

    if oldStream == True:
        sendVideo(header, data)
        #decodeVideo(data)
    elif oldStreamer == True and oldStream == False:
        newStream = []
        newStream.append(header[2:5])
        newStream.append("Video")
        oldStreamerID[1].append(newStream)
        sendVideo(header, data)
    else:
        newStreamer = []
        newStreamer.append(header[2:4])
        streams = []
        newStream = []
        newStream.append(header[2:5])
        newStream.append("Video")
        newStreamer.append(streams)
        streams.append(newStream)
        servers.append(newStreamer)
        sendVideo(header, data)
        #decodeVideo(data)

def sendImage(sentInfo, address):
    idByte = (int("0010", 2))
    idByte = idByte.to_bytes(1, 'big')

    typeByte = (int("0000", 2))
    typeByte = typeByte.to_bytes(1, 'big')

    streamBytes = header[2:7]
    newHeader = idByte + typeByte + streamBytes

    for i in clients:
        for j in i[1]:
            if j == header[2:5]:
                bytesToSend = newHeader + data
                UDPBrokerSocket.sendto(bytesToSend, i[0])

def processImage(sentInfo, address):
    header = sentInfo[:7]
    data = sentInfo[7:len(sentInfo)]
    oldStream = False
    oldStreamer = False
    oldStreamerID = 0
    oldStreamID = 0
    for i in servers:
        if i[0] == header[2:4]:
            oldStreamer = True
            oldStreamerID = i
            for j in i[1]:
                if j[0] == header[2:5]:
                    oldStream = True
                    oldStreamID = j

    if oldStream == True:
        sendImage(header, data)
        oldStreamID[2] = int.from_bytes(header[5:7], 'big')
        #decodeVideo(data)
    elif oldStreamer == True and oldStream == False:
        newStream = []
        newStream.append(header[2:5])
        newStream.append("Image")
        newStream.append(int.from_bytes(header[5:7], 'big'))
        oldStreamerID[1].append(newStream)
        sendImage(header, data)
    else:
        newStreamer = []
        newStreamer.append(header[2:4])
        streams = []
        newStream = []
        newStream.append(header[2:5])
        newStream.append("Image")
        newStream.append(int.from_bytes(header[5:7], 'big'))
        newStreamer.append(streams)
        streams.append(newStream)
        servers.append(newStreamer)
        sendImage(header, data)

def sendMessage(header, data):
    idByte = (int("0010", 2))
    idByte = idByte.to_bytes(1, 'big')

    typeByte = (int("0011", 2))
    typeByte = typeByte.to_bytes(1, 'big')

    streamBytes  = header[2:7]
    newHeader   = idByte + typeByte + streamBytes

    for i in clients:
        for j in i[1]:
            if j == header[2:5]:
                bytesToSend = newHeader + data
                UDPBrokerSocket.sendto(bytesToSend, i[0])

def processMessage(sentInfo, address):
    header = sentInfo[:7]
    data = sentInfo[7:len(sentInfo)]
    oldStream = False
    oldStreamer = False
    oldStreamerID = 0
    oldStreamID = 0
    for i in servers:
        if i[0] == header[2:4]:
            oldStreamer = True
            oldStreamerID = i
            for j in i[1]:
                if j[0] == header[2:5]:
                    oldStream = True
                    oldStreamID = j

    if oldStream == True:
        sendMessage(header, data)
        oldStreamID[2] = int.from_bytes(header[5:7], 'big')
        # decodeVideo(data)
    elif oldStreamer == True and oldStream == False:
        newStream = []
        newStream.append(header[2:5])
        newStream.append("Message")
        newStream.append(int.from_bytes(header[5:7], 'big'))
        oldStreamerID[1].append(newStream)
        sendMessage(header, data)
    else:
        newStreamer = []
        newStreamer.append(header[2:4])
        streams = []
        newStream = []
        newStream.append(header[2:5])
        newStream.append("Message")
        newStream.append(int.from_bytes(header[5:7], 'big'))
        newStreamer.append(streams)
        streams.append(newStream)
        servers.append(newStreamer)
        sendMessage(header, data)

def sendAudio(header, data):
    idByte = (int("0010", 2))
    idByte = idByte.to_bytes(1, 'big')

    typeByte = (int("0100", 2))
    typeByte = typeByte.to_bytes(1, 'big')

    streamBytes = header[2:7]
    newHeader = idByte + typeByte + streamBytes

    for i in clients:
        for j in i[1]:
            if j == header[2:5]:
                bytesToSend = newHeader + data
                UDPBrokerSocket.sendto(bytesToSend, i[0])

def processAudio(sentInfo, address):
    header = sentInfo[:7]
    data = sentInfo[7:len(sentInfo)]
    oldStream = False
    oldStreamer = False
    oldStreamerID = 0
    oldStreamID = 0
    for i in servers:
        if i[0] == header[2:4]:
            oldStreamer = True
            oldStreamerID = i
            for j in i[1]:
                if j[0] == header[2:5]:
                    oldStream = True
                    oldStreamID = j


    if oldStream == True:
        if oldStreamID[2] >= header[6]:
            print("Old frame, dropping")
        else:
            sendAudio(header, data)
            oldStreamID[2] = int.from_bytes(header[5:7],'big')
        # decodeVideo(data)
    elif oldStreamer == True and oldStream == False:
        newStream = []
        newStream.append(header[2:5])
        newStream.append("Audio")
        newStream.append(int.from_bytes(header[5:7],'big'))
        oldStreamerID[1].append(newStream)
        sendAudio(header, data)
    else:
        newStreamer = []
        newStreamer.append(header[2:4])
        streams = []
        newStream = []
        newStream.append(header[2:5])
        newStream.append("Audio")
        newStream.append(int.from_bytes(header[5:7],'big'))
        newStreamer.append(streams)
        streams.append(newStream)
        servers.append(newStreamer)
        sendAudio(header, data)


def handleServer(sentInfo, address):
    header = sentInfo[:6]
    #data = sentInfo[6:len(sentInfo)]

    if header[1] == 1:
        processMessage(sentInfo,address)
    elif header[1] == 2:
        processVideo(sentInfo,address)
    elif header[1] == 3:
        processImage(sentInfo, address)
    elif header[1] == 4:
        processAudio(sentInfo, address)



print("Broker Start!")

localIP     = "broker"
localPort   = 50002
bufferSize  = 52428800

msgFromBroker       = "Howdy folks, broker here"
bytesToSend         = str.encode(msgFromBroker)

UDPBrokerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPBrokerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000000)

# Bind to address and ip
UDPBrokerSocket.bind((localIP, localPort))

clients = []
servers = []

while (True):
    bytesAddressPair = UDPBrokerSocket.recvfrom(bufferSize)
    sentInfo = bytesAddressPair[0]
    address = bytesAddressPair[1]

    header = sentInfo[:5]
    data = sentInfo[5:len(sentInfo)]
    #print(header)
    #print(sentInfo)

    #print(header[0])
    if header[0] == 0:
        #print("Verified client")
        handleClient(sentInfo, address)
    elif header[0] == 1:
        #print("Verified Server")
        handleServer(sentInfo, address)

    #if cv2.waitKey(10) == 13:
    #    cv2.destroyAllWindows()

    # Sending a reply to client
    #UDPServerSocket.sendto(bytesToSend, address)