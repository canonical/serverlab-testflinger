#!/bin/bash
set -x
# convenience functions
#
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ServerAliveInterval=30 -o ServerAliveCountMax=3"
_put() {
    scp $SSH_OPTS $1 ubuntu@$DEVICE_IP:$2
}
_get() {
    scp $SSH_OPTS ubuntu@$DEVICE_IP:$1 $2
}
_run() {
    ssh $SSH_OPTS ubuntu@$DEVICE_IP "$@"
}
wait_for_ssh() {
    loopcnt=0
    until timeout 10 ssh $SSH_OPTS ubuntu@$DEVICE_IP /bin/true
    do
        echo "Testing to see if system is back up"
        loopcnt=$((loopcnt+1))
        if [ $loopcnt -gt 40 ]; then
            echo "ERROR: Timeout waiting for ssh!"
            exit 1
        fi
        sleep 30
    done

}
## Not used currently, but included for future use when we start adding snaps.
wait_for_snap_complete() {
    loopcnt=0
    until [ -z "$(ssh $SSH_OPTS $DEVICE_IP 'sudo snap changes | grep Doing' )" ] && [ "$(ssh $SSH_OPTS $DEVICE_IP echo true)" = "true" ]
    do
        loopcnt=$((loopcnt+1))
        if [ $loopcnt -gt 20 ]; then
            echo "ERROR: Timeout waiting for snap install!"
            exit 1
        fi
        sleep 30
    done
}
_run_retry() {
    # Retry running a command if any failure occurs
    loopcnt=0
    _run "$@"
    RC="$?"
    while [ $RC -ne 0 ]
    do
        loopcnt=$((loopcnt+1))
        if [ $loopcnt -gt 30 ]; then
            echo "ERROR: retry limit reached!"
            exit 1
        fi
        sleep 30
        _run "$@"
        RC="$?"
    done
}

# May not be necessary, but doesn't hurt to wait just in case it's
# an old, slow server
sleep 0
wait_for_ssh

# Perform any extra platform-specific setup commands here

echo "Setting up the SUT..."
echo "Initial Kernel Version: $(_run "uname -r")"
_run "sudo DEBIAN_FRONTEND=noninteractive apt-get -qq -f install"
if [ "$(_run "uname -p")" == "ppc64le" ] ; then
    APT_URL="http://ports.ubuntu.com/ubuntu-ports/"
else
    APT_URL="http://archive.ubuntu.com/ubuntu/"
fi
_run "echo deb $APT_URL focal-proposed main universe | sudo tee -a /etc/apt/sources.list"
_run "sudo DEBIAN_FRONTEND=noninteractive apt-get -qq update && sudo DEBIAN_FRONTEND=noninteractive apt-get -qq -y dist-upgrade"
echo "Current installed kernels:"
_run "dpkg -l |grep linux-image"

# Reboot and wait for the machine to come back to us
echo "Rebooting Now"
_run sudo shutdown -r
echo "Waiting for SUT to become responsive..."
wait_for_ssh

echo "Current Kernel Version: $(_run "uname -r")"

# create a launcher template
cat <<EOF >checkbox.tmpl
# Please keep the indents below, for yaml formatting/templating
[launcher]
app_id = com.canonical.certification:certification-server
launcher_version = 1
stock_reports = submission_files, certification
local_submission = yes

[environment]
TEST_TARGET_IPERF = 10.1.16.10,10.1.16.15,10.1.16.20,10.1.11.230,10.1.11.235,10.1.11.231,10.1.11.236,10.245.128.3

[test plan]
unit = com.canonical.certification::server-regression
forced = yes

[test selection]
forced = yes

[ui]
output = hide-resource-and-attachment
type = silent
auto_retry = yes
max_attempts = 2

[config]
config_filename = canonical-certification.conf

[transport:certification]
type = submission-service
secure_id = $HEXR_DEVICE_SECURE_ID

[report:upload to submission service]
transport = certification
exporter = tar

EOF
cheetah fill --env checkbox.tmpl -p > checkbox.conf

#Add a custom launcher if specified
cat <<EOF >custom.launcher

EOF
if [ "$(cat custom.launcher |wc -l)" -gt "1" ]; then
    _put custom.launcher launcher
fi

#Get kernel version for description and final output
UNAME_KERNEL_VER=$(_run 'uname -r')
KERNEL_VER=$(_run "dpkg -l |grep -m1 $UNAME_KERNEL_VER|awk '{print \$3}'")
echo "Current Kernel Version: $KERNEL_VER"

# Merge the launcher we downloaded with checkbox.conf
python3 -c "import  configparser;c=configparser.ConfigParser();c.optionxform=str;c.read('launcher');c.read('checkbox.conf');c.write(open('launcher','wt'))"

export DESCRIPTION="Focal Fossa GA Regression Test: `date +%Y-%b-%d-%H:%M:%S` Kernel: $KERNEL_VER"
[ ! -z "$NVDRV_FULL_VER" ] && export DESCRIPTION="$DESCRIPTION Driver: $NVDRV_FULL_VER"
# Add the description to the launcher
python3 -c "import configparser;c=configparser.ConfigParser();c.optionxform=str;c.read('launcher');c['launcher']['session_desc']='$DESCRIPTION';c.write(open('launcher','wt'))"

echo "DEBUG: DUMPING ENV NOW:"
env
echo

echo "DEBUG: DUMPING SUT ENV NOW:"
_run "env"
echo

echo "Starting actual test run now"
PYTHONUNBUFFERED=1 checkbox-cli remote $DEVICE_IP launcher
EXITCODE=$?

# Put necessary files into artifacts folder
mkdir -p artifacts

# IF EGX artifiacts exist, we need to retrieve them
EGX_RESULTS_PATH=`_run "find /opt/NGC.Ready/result.*.gz"`
if [ ! -z $EGX_RESULTS_PATH ]; then
    echo "Found $EGX_RESULTS_PATH, saving it now"
    EGX_RES_FILE=`basename $EGX_RESULTS_PATH`
    _get $EGX_RESULTS_PATH /root/
    EGX_FIND=`find /root -name $EGX_RES_FILE`
    mv $EGX_FIND ./artifacts/
    # find /home/ubuntu/ -name $EGX_RES_FILE -exec mv {} artifacts/ ';'
    # (find /home/ubuntu/ -name $EGX_RES_FILE > ./artifacts/$EGX_RES_FILE);
fi

# Get the rest of the artifacts
cp launcher artifacts
mv /root/.local/share/checkbox-ng/* ./artifacts
tar -xf ./artifacts/*.tar.xz

# JUNIT=`find /root/ -name 'submission_*.junit.xml'`
# SUBHTML=`find /root/ -name 'submission_*.html'`
# SUBTAR=`find /root -name 'submission_*.tar.xz'`
# SUBXLS=`find /root -name 'submission_*.xlsx'`
# mv $JUNIT ./artifacts/junit.xml
# mv $SUBHTML ./artifacts/submission.html
# mv $SUBTAR ./artifacts/submission.tar.xz
# mv $SUBXLS ./artifacts/submission.xlsx
# # find /home/ubuntu/ -name 'submission_*.junit.xml' -exec mv {} artifacts/junit.xml \;
# # find /home/ubuntu/ -name 'submission_*.html' -exec mv {} artifacts/submission.html \;
# # find /home/ubuntu/ -name 'submission_*.xlsx' -exec mv {} artifacts/submission.xlsx \;
# # find /home/ubuntu/ -name 'submission_*.tar.xz' -exec mv {} artifacts/submission.tar.xz \;
# # find /home/ubuntu/ -name 'submission_*.junit.xml' > ./artifacts/junit.xml;
# # find /home/ubuntu/ -name 'submission_*.html' > ./artifacts/submission.html;
# # find /home/ubuntu/ -name 'submission_*.xlsx' > ./artifacts/submission.xlsx;
# # find /home/ubuntu/ -name 'submission_*.tar.xz' > ./artifacts/submission.tar.xz;
# tar -xf ./artifacts/submission.tar.xz

# fix EFI boot order issue (workaround)
ROOT_DISK=$( _run grep "/boot/efi" /proc/mounts |cut -d ' ' -f 1|grep -o '.*[^0-9]' )
echo "Zeroing Disk $ROOT_DISK"
_run sudo sgdisk -Z $ROOT_DISK

#Power down system so we know it is complete
echo "Powering down the SUT now..."
_run sudo poweroff
