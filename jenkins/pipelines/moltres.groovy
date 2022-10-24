def sutAgent = 'wildorange'

def release = 'focal'

def globalTimeout = 172800

def outputTimeout = 172800

def testCMD = 
    'ssh -o StrictHostKeyChecking=no ubuntu@$DEVICE_IP \
    /usr/bin/checkbox-cli run com.canonical.certification::usb'

def testCMDFileSRU = '/opt/sru_01.sh'

def testCMDFileEGX = '/opt/egx_01.sh'

def yamlFile = 
    """
    job_queue: ${sutAgent}
    global_timeout: ${globalTimeout}
    output_timeout: ${outputTimeout}
    provision_data:
      distro: ${release}
    test_data:
      test_cmds: |-
        ${testCMDFileSRU}
    """

def cmdPrefix = 
    'testflinger-cli --server http://10.245.128.10:8000'

def testExec = 
    "${cmdPrefix} submit -q /home/jenkins/job.yaml"

def retCode =
    "awk '{if(/test_status/) print \$2}' | tail -1"

// pass vars between stages
def jobID

def testStatus

pipeline {
    agent { label sutAgent }

    stages {
        stage('write config') {
            steps {
                script {
                    if (fileExists('/home/jenkins/job.yaml')) {
                        echo 'job.yaml exists; overwriting'
                        sh 'rm /home/jenkins/job.yaml'
                    }

                    writeFile file: '/home/jenkins/job.yaml', text: yamlFile
                    echo 'current config:'
                    echo readFile('/home/jenkins/job.yaml')
                }
            }
        }

        stage('execute job') {
            steps {
                script {
                    jobID = sh(
                        script: testExec,
                        returnStdout: true).trim()

                    echo "Job ID: ${jobID}"
                }
            }
        }

        stage('poll job output') {
            steps {
                script {
                    sh "${cmdPrefix} poll ${jobID}"
                }
            }
        }

        stage('parse job results') {
            steps {
                script {
                    testStatus = sh(
                        script: "${cmdPrefix} results ${jobID} | ${retCode}",
                        returnStdout: true).trim().toInteger()

                    echo "Job exit status: ${testStatus}"

                    if (testStatus) {
                        error('Job FAILED!')
                    } else {
                        echo 'Job PASSED!'
                    }
                }
            }
        }
    }
}