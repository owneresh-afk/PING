FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    ttyd tmux python3 python3-pip \
    git wget curl ffmpeg aria2 unzip nano

EXPOSE 10000

CMD ["ttyd","-W","-p","10000","bash"]
