FROM ubuntu:20.10

# Keep upstart from complaining
RUN dpkg-divert --local --rename --add /sbin/initctl
RUN ln -sf /bin/true /sbin/initctl

# Let the conatiner know that there is no tty
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get -y upgrade

# Basic Requirements
RUN apt-get -y install nginx pwgen python3 python3-pip curl git unzip vim

RUN pip3 install web3==5.13.1

# nginx config
RUN sed -i -e"s/keepalive_timeout\s*65/keepalive_timeout 2/" /etc/nginx/nginx.conf
RUN sed -i -e"s/keepalive_timeout 2/keepalive_timeout 2;\n\tclient_max_body_size 100m/" /etc/nginx/nginx.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# nginx site conf
ADD sample/nginx-site.conf /etc/nginx/sites-available/default
COPY abi /etc/

ADD ./endpoints.py /etc/endpoints.py
ADD ./periodic_config_update.py /etc/periodic_config_update.py
ADD ./VERSION /etc/VERSION

# Initialization and Startup Script
ADD ./start.sh /start.sh
RUN chmod 755 /start.sh

CMD ["/bin/bash", "/start.sh"]
