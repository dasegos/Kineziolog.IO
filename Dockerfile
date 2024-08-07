FROM python:3.12
RUN mkdir /bot
WORKDIR /bot
COPY requirements.txt .
RUN pip3 install --upgrade setuptools
RUN pip3 install -r requirements.txt
# To use Aiogram Calendar
# (installing and setting locales)
RUN apt-get update && \  
    apt-get install -y locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales
ENV LANG ru_RU.UTF-8
ENV LC_TIME ru_RU.UTF-8
# To use apscheduler (setting
# the timezone in docker container)
RUN rm -rf /etc/localtime
RUN ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN echo 'Europe/Moscow' > /etc/timezone
COPY . .