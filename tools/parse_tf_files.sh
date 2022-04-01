#!/usr/bin/bash

########################
# RUN FROM DOCKER ROOT #
########################

# todo:
#  move to python

shopt -s extglob

# replicate authorized_keys
SRC_KEY_FILE=~/.ssh/authorized_keys
DST_KEY_FILE=./ssh/authorized_keys
DST_SSH_DIR=ssh
if ! test -f $DST_KEY_FILE; then
	if ! test -d $DST_SSH_DIR; then
		echo "> creating project ssh dir"
		mkdir ./$DST_SSH_DIR
	fi
	echo "> copying ssh authorized_keys"
	cp $SRC_KEY_FILE ./$DST_SSH_DIR
	chmod 644 $DST_KEY_FILE
else
	echo "> ssh authorized_keys present"
fi

# create sut dir
SUT_DIR=sut
if ! test -d $SUT_DIR; then
	echo "> creating agent base directory"
	mkdir ./$SUT_DIR
fi

# copy tf-agent files
AGENT_CONF=./sut/!(*snappy*).conf
AGENT_DIR=./sut/agent
# if ! test -f $AGENT_CONF
if ! test -d $AGENT_DIR; then
	echo "> creating agent conf directory"
	mkdir $AGENT_DIR
fi
echo "> copying agent confs"
cp $AGENT_CONF $AGENT_DIR

# copy snappy-agent files
SNAPPY_F=./sut/*snappy*.y*ml
SNAPPY_DIR=./sut/snappy
if ! test -d $SNAPPY_DIR; then
	echo "> creating snappy-agent directory"
	mkdir $SNAPPY_DIR
fi
echo "> copying agent snappy-agent files"
cp $SNAPPY_F $SNAPPY_DIR

# copy tf-cli files	
CLI_F=./sut/!(*snappy*).y*ml
CLI_DIR=./sut/cli
if ! test -d $CLI_DIR; then
	echo "> creating snappy-agent directory"
	mkdir $CLI_DIR
fi
echo "> copying agent cli files"
cp $CLI_F $CLI_DIR
