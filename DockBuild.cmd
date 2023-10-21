docker build -t mynetimage .
docker rm -f server
docker rm -f client
docker rm -f clientwo
docker rm -f broker
docker rm -f fbi
docker rm -f cia
docker rm -f cliiient
docker create --name server -ti --cap-add=all mynetimage /bin/bash
docker create --name client -ti --cap-add=all mynetimage /bin/bash
docker create --name clientwo -ti --cap-add=all mynetimage /bin/bash
docker create --name broker -ti --cap-add=all mynetimage /bin/bash
docker create --name fbi -ti --cap-add=all mynetimage /bin/bash
docker create --name cia -ti --cap-add=all mynetimage /bin/bash
docker create --name cliiient -ti --cap-add=all mynetimage /bin/bash
docker network connect mynet client
docker network connect mynet clientwo
docker network connect mynet server
docker network connect mynet broker
docker network connect mynet fbi
docker network connect mynet cia
docker network connect mynet cliiient
docker start -i server