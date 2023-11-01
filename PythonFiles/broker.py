
import socket
import sys
import select
import cv2, numpy, pickle, os
import keyboard

blank = (int("0000", 2))
blank = blank.to_bytes(2, 'big')
blankByte = (int("0000", 2))
blankByte = blankByte.to_bytes(1, 'big')

idByte = (int("0010",2))
idByte = idByte.to_bytes(1,'big')

messageBlank = blank + blank + blank

imageByte = (int("0000", 2))
imageByte = imageByte.to_bytes(1, 'big')

ackByte = (int("1111", 2))
ackByte = ackByte.to_bytes(1, 'big')

messageByte = (int("0101", 2))
messageByte = messageByte.to_bytes(1, 'big')

textByte = (int("0011", 2))
textByte = textByte.to_bytes(1, 'big')

audioByte = (int("0100", 2))
audioByte = audioByte.to_bytes(1, 'big')

ackByte = (int("1111", 2))
ackByte = ackByte.to_bytes(1, 'big')

def decodeMessage(messageData):
    data = messageData.decode()
    receivedMsg = "Message from sender:{}".format(data)
    print(receivedMsg)


def addToOldSubscription(header, client):
    for i in client[1]:
        if i == header[2:6]:
            print('Already subscribed')
            msg = "You are already subscribed to that stream"
            fileHeader = idByte + ackByte + messageBlank
            data = fileHeader + str.encode(msg)
            UDPBrokerSocket.sendto(data, client[0])
            return
    addSubscription(header,client)


def addSubscription(header, client):
    for i in servers:
        if i[0] == header[2:5]:
            for j in i[1]:
                if header[2:6] == j[0]:
                    client[1].append(header[2:6])
                    msg = "You have successfully been subscribed"
                    fileHeader = idByte + ackByte + messageBlank
                    data = fileHeader + str.encode(msg)
                    UDPBrokerSocket.sendto(data, client[0])
                    return
    msg = "Stream does not exist"
    fileHeader = idByte + ackByte + messageBlank
    data = fileHeader + str.encode(msg)
    UDPBrokerSocket.sendto(data, client[0])


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
               msg += j[0].hex() + " - " + j[1] + "\n"
        if msg == "Streams: Note some streams may not be currently running\n":
            msg = "We have no active streams right now :("

    data = str.encode(msg)

    dummyBits = int("000000000000", 2)
    dummyBits = dummyBits.to_bytes(4, 'big')

    header = idByte + ackByte + dummyBits + blank
    bytesToSend = header + data

    UDPBrokerSocket.sendto(bytesToSend, port)

def streamToString(stream):
    msg = ""
    msg += stream.hex()
    return msg

def unsubServer(header, port):
    for i in clients:
        if i[0] == port:
            if header[2:6] in i[1]:
                i[1].remove(header[2:6])
                msg = "You have successfully been unsubscribed"
                fileHeader = idByte + ackByte + messageBlank
                data = fileHeader + str.encode(msg)
                UDPBrokerSocket.sendto(data, i[0])

def disconnectClient(header,port):
    for i in clients:
        if i[0] == port:
            msg = "You have successfully been disconnected"
            fileHeader = idByte + ackByte + messageBlank
            data = fileHeader + str.encode(msg)
            UDPBrokerSocket.sendto(data, i[0])
            clients.remove(i)




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
    elif header[1] == 6:
        disconnectClient(header,port)




def sendVideo(header, data):

    typeByte = (int("0001", 2))
    typeByte = typeByte.to_bytes(1, 'big')

    streamBytes  = header[2:8]
    newHeader   = idByte + typeByte + streamBytes

    for i in clients:
        for j in i[1]:
            if j == header[2:6]:

                bytesToSend = newHeader + data
                UDPBrokerSocket.sendto(bytesToSend, i[0])




def processVideo(sentInfo, address):
    header = sentInfo[:8]
    data = sentInfo[8:len(sentInfo)]
    oldStream = False
    oldStreamer = False
    oldStreamerID = 0
    for i in servers:
        if i[0] == header[2:5]:
            oldStreamer = True
            oldStreamerID = i
            for j in i[1]:
                if j[0] == header[2:6]:
                    oldStream = True

    if oldStream == True:
        sendVideo(header, data)
    elif oldStreamer == True and oldStream == False:
        newStream = [header[2:6],"Video"]
        oldStreamerID[1].append(newStream)
        sendVideo(header, data)
    else:
        newStream = [header[2:6],"Video"]
        streams = [newStream]
        newStreamer = [header[2:5],streams]
        servers.append(newStreamer)
        sendVideo(header, data)

def sendImage(sentInfo, data):

    streamBytes = sentInfo[2:8]
    newHeader = idByte + imageByte + streamBytes

    for i in clients:
        for j in i[1]:
            if j == sentInfo[2:6]:
                bytesToSend = newHeader + data
                UDPBrokerSocket.sendto(bytesToSend, i[0])

def processImage(sentInfo, address):
    header = sentInfo[:8]
    data = sentInfo[8:len(sentInfo)]
    oldStream = False
    oldStreamer = False
    oldStreamerID = 0
    for i in servers:
        if i[0] == header[2:5]:
            oldStreamer = True
            oldStreamerID = i
            for j in i[1]:
                if j[0] == header[2:6]:
                    oldStream = True

    if oldStream == True:
        sendImage(header, data)
    elif oldStreamer == True and oldStream == False:
        newStream = [header[2:6],"Image"]
        oldStreamerID[1].append(newStream)
        sendImage(header, data)
    else:
        newStream = [header[2:6],"Image"]
        streams = [newStream]
        newStreamer = [header[2:5],streams]
        servers.append(newStreamer)
        sendImage(header, data)

def sendMessage(header, data):

    streamBytes  = header[2:8]
    newHeader   = idByte + textByte + streamBytes

    for i in clients:
        for j in i[1]:
            if j == header[2:6]:
                bytesToSend = newHeader + data
                UDPBrokerSocket.sendto(bytesToSend, i[0])

def processMessage(sentInfo, address):
    header = sentInfo[:8]
    data = sentInfo[8:len(sentInfo)]
    oldStream = False
    oldStreamer = False
    oldStreamerID = 0
    for i in servers:
        if i[0] == header[2:5]:
            oldStreamer = True
            oldStreamerID = i
            for j in i[1]:
                if j[0] == header[2:6]:
                    oldStream = True

    if oldStream == True:
        sendMessage(header, data)
    elif oldStreamer == True and oldStream == False:
        newStream = [header[2:6],"Message"]
        oldStreamerID[1].append(newStream)
        sendMessage(header, data)
    else:
        newStream = [header[2:6],"Message"]
        streams = [newStream]
        newStreamer = [header[2:5],streams]
        servers.append(newStreamer)
        UDPBrokerSocket.sendto(idByte + ackByte + sentInfo[2:6], address)
        sendMessage(header, data)

def sendAudio(header, data):

    streamBytes = header[2:8]
    newHeader = idByte + audioByte + streamBytes

    for i in clients:
        for j in i[1]:
            if j == header[2:6]:
                bytesToSend = newHeader + data
                UDPBrokerSocket.sendto(bytesToSend, i[0])

def processAudio(sentInfo, address):
    header = sentInfo[:8]
    data = sentInfo[8:len(sentInfo)]
    oldStream = False
    oldStreamer = False
    oldStreamerID = 0
    for i in servers:
        if i[0] == header[2:5]:
            oldStreamer = True
            oldStreamerID = i
            for j in i[1]:
                if j[0] == header[2:6]:
                    oldStream = True


    if oldStream == True:
        sendAudio(header, data)
    elif oldStreamer == True and oldStream == False:
        newStream = [header[2:6],"Audio"]
        oldStreamerID[1].append(newStream)
        sendAudio(header, data)
    else:
        newStream = [header[2:6],"Audio"]
        streams = [newStream]
        newStreamer = [header[2:5],streams]
        servers.append(newStreamer)
        sendAudio(header, data)

def removeStream(sentInfo):
    for i in servers:
        if i[0] == sentInfo[2:5]:
            for j in i[1]:
                if sentInfo[2:6] == j[0]:
                    i[1].remove(j)

    for i in clients:
        if sentInfo[2:6] in i[1]:
            i[1].remove(sentInfo[2:6])
            fileHeader = idByte + messageByte + messageBlank
            msg = str.encode("We apologise, you have been unsubscribed from stream " +
                             streamToString(sentInfo[2:6]) + " as it has been disconnected")
            dataToSend = fileHeader + msg
            UDPBrokerSocket.sendto(dataToSend,i[0])


def disconnectServer(sentInfo):
    for i in servers:
        if sentInfo[2:5] == i[0]:
            print("Server found, disconnecting")
            servers.remove(i)

    for i in clients:
        for j in i[1]:
            print("Checking")
            if sentInfo[2:5] == j[:3]:
                print("Found")
                i[1].remove(j)
                fileHeader = idByte + messageByte + messageBlank
                msg = str.encode("We apologise, you have been unsubscribed from stream " +
                                 streamToString(sentInfo[2:6]) + " as the server running it has disconnected")
                dataToSend = fileHeader + msg
                UDPBrokerSocket.sendto(dataToSend, i[0])


def handleServer(sentInfo, address):
    header = sentInfo[:8]

    if header[1] == 1:
        processMessage(sentInfo,address)
    elif header[1] == 2:
        processVideo(sentInfo,address)
    elif header[1] == 3:
        processImage(sentInfo, address)
    elif header[1] == 4:
        processAudio(sentInfo, address)
    elif header[1] == 5:
        removeStream(sentInfo)
    elif header[1] == 6:
        print("Starting disconnect")
        disconnectServer(sentInfo)



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

    if sentInfo[0] == 0:
        handleClient(sentInfo, address)
    elif sentInfo[0] == 1:
        handleServer(sentInfo, address)