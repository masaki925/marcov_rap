#Grab the latest alpine image
FROM alpine:latest

RUN apk add --update --no-cache build-base

ENV MECAB_VERSION 0.996
ENV IPADIC_VERSION 2.7.0-20070801
ENV mecab_url https://drive.google.com/uc?export=download&id=0B4y35FiV1wh7cENtOXlicTFaRUE
ENV ipadic_url https://drive.google.com/uc?export=download&id=0B4y35FiV1wh7MWVlSDBCSXZMTXM
ENV build_deps 'curl git bash file sudo openssh'
ENV dependencies 'openssl'


RUN apk add --update --no-cache ${build_deps} \
  # Install dependencies
  && apk add --update --no-cache ${dependencies} \
  # Install MeCab
  && curl -SL -o mecab-${MECAB_VERSION}.tar.gz ${mecab_url} \
  && tar zxf mecab-${MECAB_VERSION}.tar.gz \
  && cd mecab-${MECAB_VERSION} \
  && ./configure --enable-utf8-only --with-charset=utf8 \
  && make \
  && make install \
  && cd \
  # Install IPA dic
  && curl -SL -o mecab-ipadic-${IPADIC_VERSION}.tar.gz ${ipadic_url} \
  && tar zxf mecab-ipadic-${IPADIC_VERSION}.tar.gz \
  && cd mecab-ipadic-${IPADIC_VERSION} \
  && ./configure --with-charset=utf8 \
  && make \
  && make install \
  && cd \
  # Install Neologd
  && git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git \
  && mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n -y \
  # Clean up
  && apk del ${build_deps} \
  && rm -rf \
    mecab-${MECAB_VERSION}* \
    mecab-${IPADIC_VERSION}* \
    mecab-ipadic-neologd

# Install python and pip
RUN apk add --no-cache --update python3 py3-pip bash
ADD ./webapp/requirements.txt /tmp/requirements.txt

RUN apk add --update --no-cache swig python3-dev openblas-dev

# Install dependencies
RUN pip3 install --no-cache-dir -q -r /tmp/requirements.txt

# Add our code
ADD ./webapp /opt/webapp/
WORKDIR /opt/webapp

# Expose is NOT supported by Heroku
# EXPOSE 5000 		

# Run the image as a non-root user
RUN adduser -D myuser
USER myuser

# Run the app.  CMD is required to run on Heroku
# $PORT is set by Heroku			
CMD gunicorn --bind 0.0.0.0:$PORT wsgi 

