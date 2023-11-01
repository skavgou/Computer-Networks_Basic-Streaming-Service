# based on https://pythontic.com/modules/socket/udp-client-server-example
import random
import socket
import sys
import select
import cv2, numpy as np, pickle, os
#import keyboard
import time
import pydub
from pydub import AudioSegment
#import sounddevice as sd
#import audio2numpy as a2n


idByte = (int("0001",2))
idByte = idByte.to_bytes(1,'big')

imageByte = (int("0011", 2))
imageByte = imageByte.to_bytes(1, 'big')
videoByte = (int("0010", 2))
videoByte = videoByte.to_bytes(1, 'big')
textByte = (int("0001", 2))
textByte = textByte.to_bytes(1, 'big')
audioByte = (int("0100", 2))
audioByte = audioByte.to_bytes(1, 'big')
removeByte = (int("0101", 2))
removeByte = removeByte.to_bytes(1, 'big')
dcByte = (int("0110", 2))
dcByte = dcByte.to_bytes(1, 'big')
blank = (int("0000", 2))
blank = blank.to_bytes(2, 'big')
blankStream = (int("0000", 2))
blankStream = blankStream.to_bytes(1, 'big')

sampleVid = cv2.VideoCapture('Yoink.mp4')
sample1Length = int(sampleVid.get(cv2.CAP_PROP_FRAME_COUNT))
vid1Type = "Video"
vid1ID = (int("0001", 2))
vid1ID = vid1ID.to_bytes(1, 'big')
vid1Data = []
vid1Data.append(vid1Type)
vid1Data.append(vid1ID)
vid1Data.append(sampleVid)
vid1Data.append(sample1Length - 1)
vid1Data.append(0)

sampleAudio = AudioSegment.from_mp3('Yoink.mp3')
audio1Type = "Audio"
audio1ID = (int("0101", 2))
audio1ID = audio1ID.to_bytes(1, 'big')
audio1 = pydub.AudioSegment.from_mp3('Yoink.mp3')
audio1Array = np.array(audio1.get_array_of_samples())
audio1Array = np.array_split(audio1Array, sample1Length)
audio1Data = []
audio1Data.append(audio1Type)
audio1Data.append(audio1ID)
audio1Data.append(audio1Array)
audio1Data.append(sample1Length - 1)
audio1Data.append(0)



sampleVid2 = cv2.VideoCapture('Spinnnn.mp4')
sample2Length = int(sampleVid2.get(cv2.CAP_PROP_FRAME_COUNT))
vid2Type = "Video"
vid2ID = (int("0010", 2))
vid2ID = vid2ID.to_bytes(1, 'big')
vid2Data = []
vid2Data.append(vid2Type)
vid2Data.append(vid2ID)
vid2Data.append(sampleVid2)
vid2Data.append(sample2Length - 1)
vid2Data.append(0)

sampleImage = cv2.imread('Model_Photo.jpg')
image1Type = "Image"
image1ID = (int("0011", 2))
image1ID = image1ID.to_bytes(1, 'big')
image1Data = []
image1Data.append(image1Type)
image1Data.append(image1ID)
image1Data.append(sampleImage)

sampleText = open('text.txt','r')
text1Type = "Text"
text1ID = (int("0100", 2))
text1ID = text1ID.to_bytes(1, 'big')
sampleTextData = []
sampleTextData.append(text1Type)
sampleTextData.append(text1ID)
sampleTextData.append(sampleText)
sampleTextData.append(0)



activeStreams = []
currentTime = 0
streamerIDNum = (int(random.randint(0,16777216))).to_bytes(3, 'big')



def encodeToArray(video):
    print("Encoding Video " + str(video[1]))
    vidFrames = []
    for i in range(video[3]):
        print(str(i))
        frameFound, frame = video[2].read()
        ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
        encodedFrame = pickle.dumps(buffer)
        vidFrames.append(encodedFrame)
        video.append(vidFrames)


def encodeTextArray(textData):
    textArray = []
    while True:
        line = textData[2].readline()
        if not line:
            break
        line = line.split(":")
        if "\n" not in line[1]:
            line[1] += "\n"
        textArray.append(line[1])
        textArray.append(int(line[0]))
        textData[3] += 2
    textData.append(textArray)
    textData.append(0)
    textData.append(0)
    #print(textData)

#def sendAudio(audio):




def sendText(text):
    if text[5] < len(text[4]):
        if isinstance(text[4][text[5]], str):
            #print("Sending " + text[4][text[5]])
            frameNo = text[5].to_bytes(2,'big')
            fileHeader = idByte + textByte + streamerIDNum + text[1] + frameNo
            data = str.encode(text[4][text[5]])
            bytesToSend = fileHeader + data
            UDPServerSocket.sendto(bytesToSend, brokerAddressPort)
            text[5] += 1
            text[6] = text[4][text[5]]
        elif isinstance(text[4][text[5]], int):
            text[6] -= 1
            if text[6] == 0:
                text[5] += 1
        else:
            text[5] += 1
    else:
        text[5] = 0

def sendAudio(audio):
    frameNo = audio[4].to_bytes(2, 'big')
    fileHeader = idByte + audioByte + streamerIDNum + audio[1] + frameNo
    audioFrame = audio[2][audio[4]].tobytes()
    data = fileHeader + audioFrame
    UDPServerSocket.sendto(data, brokerAddressPort)
    audio[4] += 1
    if audio[4] == audio[3]:
        audio[4] = 0

def sendVideo(video):
    frameNo = video[4].to_bytes(2,'big')
    fileHeader = idByte + videoByte + streamerIDNum + video[1] + frameNo
    frameFound, frame = video[2].read()
    ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY),30])
    encodedFrame = pickle.dumps(buffer)
    data = fileHeader + encodedFrame

    UDPServerSocket.sendto(data, brokerAddressPort)

    #clockTime = time.perf_counter() - currentTime
    #print("Send complete, " + str(clockTime))

    video[4] += 1
    if video[4] == video[3]:
        # activeStreams.remove(video)
        video[2].set(cv2.CAP_PROP_POS_FRAMES, 0)
        video[4] = 0

def sendImage(image):
    fileHeader = idByte + imageByte + streamerIDNum + image[1] + blank
    ret, buffer = cv2.imencode(".jpg", image[2], [int(cv2.IMWRITE_JPEG_QUALITY), 30])
    encodedFrame = pickle.dumps(buffer)
    data = fileHeader + encodedFrame
    UDPServerSocket.sendto(data, brokerAddressPort)

def sendOutData():
    for i in activeStreams:
        #clockTime = time.perf_counter() - currentTime
        #print("Function called, " + str(clockTime))
        if i[0] == "Video":
            #clockTime = time.perf_counter() - currentTime
            #print("Active stream found, sending, " + str(clockTime))
            sendVideo(i)
        elif i[0] == "Image":
            sendImage(i)
        elif i[0] == "Text":
            sendText(i)
        elif i[0] == "Audio":
            sendAudio(i)



def send(type):
    filler = "                  "
    type += filler #prevents out of bounds errors
    if type[0:4] == "send":
        if type[5:8] == "msg":
            if sampleTextData not in activeStreams:
                activeStreams.append(sampleTextData)
            else:
                print("Stream already active")
        elif type[5:10] == "video":
            if type[11] == "1":
                if vid1Data not in activeStreams:
                    activeStreams.append(vid1Data)
                else:
                    print("Stream already active")
            elif type[11] == "2":
                if vid2Data not in activeStreams:
                    activeStreams.append(vid2Data)
                else:
                    print("Stream already active")
            else:
                print("Please choose a valid video number")
                print("The valid numbers are: 1,2")
        elif type[5:10] == "image":
            if image1Data not in activeStreams:
                activeStreams.append(image1Data)
            else:
                print("Stream already active")
        elif type[5:10] == "audio":
            if audio1Data not in activeStreams:
                activeStreams.append(audio1Data)
            else:
                print("Stream already active")
        else:
            print("Please choose a valid option")
            print("The valid options are: msg, video, image, audio")
    elif type[0:4] == "stop":
        fileHeader = idByte + removeByte + streamerIDNum
        if type[5:8] == "msg":
            if sampleTextData in activeStreams:
                activeStreams.remove(sampleTextData)
                fileHeader += sampleTextData[1] + blank
                data = fileHeader + str.encode("Stop request for text stream")
                UDPServerSocket.sendto(data, brokerAddressPort)
            else:
                print("Stream not currently active!")
        elif type[5:10] == "video":
            if type[11] == "1":
                if vid1Data in activeStreams:
                    activeStreams.remove(vid1Data)
                    fileHeader += vid1Data[1] + blank
                    data = fileHeader + str.encode("Stop request for video")
                    UDPServerSocket.sendto(data, brokerAddressPort)
                else:
                    print("Stream not currently active!")
            elif type[11] == "2":
                if vid2Data in activeStreams:
                    activeStreams.remove(vid2Data)
                    fileHeader += vid2Data[1] + blank
                    data = fileHeader + str.encode("Stop request for video")
                    UDPServerSocket.sendto(data, brokerAddressPort)
                else:
                    print("Stream not currently active!")
            else:
                print("Please choose a valid video number")
                print("The valid numbers are: 1,2. Try typing 'stop video 1'")
        elif type[5:10] == "image":
            if image1Data in activeStreams:
                activeStreams.remove(image1Data)
                fileHeader += image1Data[1] + blank
                data = fileHeader + str.encode("Stop request for image")
                UDPServerSocket.sendto(data, brokerAddressPort)
            else:
                print("Stream not currently active!")
        elif type[5:10] == "audio":
            if audio1Data in activeStreams:
                activeStreams.remove(audio1Data)
                fileHeader += audio1Data[1] + blank
                data = fileHeader + str.encode("Stop request for audio")
                UDPServerSocket.sendto(data, brokerAddressPort)
            else:
                print("Stream not currently active!")
        else:
            print("Please choose a valid option")
            print("The valid options are: msg, video, image, audio")
    elif type[0:10] == "disconnect":
        fileHeader = idByte + dcByte + streamerIDNum + blankStream + blank
        data = fileHeader + str.encode("Server disconnect request")
        UDPServerSocket.sendto(data, brokerAddressPort)
        activeStreams.clear()




def listen():
    msgFromBroker, addr = UDPServerSocket.recvfrom(bufferSize)
    if msgFromBroker[0] == 2 and msgFromBroker[1] == 15:
        print("ack received")


print("Server start!")

localIP     = "server"
bufferSize  = 52428800

brokerAddressPort   = ("broker", 50002)
msgFromServer       = "Hello Client!!"
bytesToSend         = str.encode(msgFromServer)

# Create a datagram socket
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000000)

print("UDP server up and listening")

#encodeToArray(vid1Data)
#encodeToArray(vid2Data)
encodeTextArray(sampleTextData)

run = True

ServerSock = [UDPServerSocket]
# Listen for incoming datagrams
while(run):
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)

    if rlist:
        user_input = sys.stdin.readline().strip()
        print(f"User input: {user_input}")
        send(user_input)

    # Check for incoming packets
    readable, _, _ = select.select(ServerSock, [], [], 0.1)

    for s in readable:
        if s is UDPServerSocket:
            listen()
    sendOutData()
