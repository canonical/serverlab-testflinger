#!/bin/bash

# VARS
testfile=$1
count=0

# Run test
jobid=$(testflinger submit "$testfile" | grep job_id | awk '{print $2}')
echo "Job started: $jobid"

# Wait 10 minutes for servers to get underway and then start polling
# for status every 60 seconds after that
echo "  Sleeping for 10 minutes for provisioning"
sleep 10m
while [ $count -le 30 ]; do
    ((count+=1))
    status=$(testflinger status "$jobid")
    if [ "$status" == "complete" ]; then
        echo "  Job completed"
        break
    elif [ $count -gt 30 ]; then
        echo "  ERROR: Job $jobid timeout after 40 minutes"
        echo "         exiting test, please check the job directly"
        exit 1
    else
        echo "  Current status: $status..." 
        sleep 60
    fi
done

provision_status=$(testflinger results "$jobid" | jq '.provision_status')
if [ $provision_status == 1 ]; then
    # Provisioning failed, discover the nodes and find the one(s) that failed
    
else
    #Provisioning passed, check on the test status now

fi

testflinger results $jobid
