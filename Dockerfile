FROM ubuntu
RUN apt-get update
RUN apt-get install -y net-tools netcat tcpdump inetutils-ping python3 wireshark
RUN apt-get install -y pip
RUN apt-get install -y ffmpeg
RUN pip3 install opencv-python
RUN pip3 install keyboard
RUN pip3 install ffmpeg
RUN pip3 install audio2numpy
RUN pip3 install pydub
RUN pip3 install sounddevice
RUN pip3 install matplotlib
RUN pip3 install pydub
COPY /PythonFiles /PythonFiles
WORKDIR /PythonFiles
ENV DISPLAY=host.docker.internal:0
ENV LIBGL_ALWAYS_INDIRECT=1
ENV XDG_RUNTIME_DIR=/tmp/foobar
CMD ["/bin/bash"]
