FROM python:3
ADD main.py /
ADD idcharger.py /
ADD settings.py /
RUN pip install requests
RUN pip install paho-mqtt
CMD [ "python", "./main.py" ]