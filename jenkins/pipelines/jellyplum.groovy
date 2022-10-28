def sutAgent = 'jellyplum'

def release = 'focal'

def globalTimeout = 172800

def outputTimeout = 172800

def testCMD = 
    'ssh -o StrictHostKeyChecking=no ubuntu@$DEVICE_IP \
    /usr/bin/checkbox-cli run com.canonical.certification::usb'

def testCMDFileSRU = '/opt/sru_01.sh'

def testCMDFileEGX = '/opt/egx_01.sh'

def apiServer = '10.245.128.10'

def apiPort = '8000'

def yamlFilePath = '/home/jenkins/job.yaml'

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
    "testflinger-cli --server http://${apiServer}:${apiPort}"

def testExec =
    "${cmdPrefix} submit -q ${yamlFilePath}"

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
                    if (fileExists("${yamlFilePath}")) {
                        echo "${yamlFilePath} exists; overwriting"
                        sh "rm ${yamlFilePath}"
                    }

                    writeFile file: "${yamlFilePath}", text: yamlFile
                    echo 'current config:'
                    echo readFile("${yamlFilePath}")
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