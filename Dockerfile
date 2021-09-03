FROM public.ecr.aws/lambda/python:3.8

RUN yum update -y

RUN python -m pip install --upgrade pip

RUN yum install amazon-linux-extras -y

# Python3 doesn't recognize this package yet. https://forums.aws.amazon.com/thread.jspa?messageID=930259
RUN PYTHON=python2 amazon-linux-extras install epel -y

RUN yum install -y gcc gcc-c++ clamav clamd clamav-update \
    && ln -s /etc/freshclam.conf /tmp/freshclam.conf

COPY function/virus-scanner.py ${LAMBDA_TASK_ROOT}/

COPY clamd.conf /etc/clamd.conf

COPY ./requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt

RUN cd ${LAMBDA_TASK_ROOT}

RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt -t .

# Force running freshclam everytime the image is being built, so new antivirus definitions are downloaded
ARG CACHEBUST=1
RUN echo $CACHEBUST
RUN freshclam

CMD [ "virus-scanner.lambda_handler" ]