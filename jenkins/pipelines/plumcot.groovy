def sutAgent = 'plumcot'

def release = 'focal'

def globalTimeout = 172800

def outputTimeout = 172800

def testCMD = 
    'ssh -o StrictHostKeyChecking=no ubuntu@$DEVICE_IP \
    /usr/bin/checkbox-cli run com.canonical.certification::usb'

def testCMDFileSRU = '/opt/sru_01.sh'

def testCMDFileEGX = '/opt/egx_01.sh'

def apiServer = 'testflinger.canonical.com'

def apiPort = '443'

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
    "testflinger-cli --server https://${apiServer}:${apiPort}"

def testExec =
    "${cmdPrefix} submit -q ${yamlFilePath}"

def agentLog = "/var/log/${sutAgent}.log"

def compltRegex = 'submissions.status'

def jobID

pipeline {
    agent { label sutAgent }

    stages {
        stage('zero logs') {
            steps {
                script {
                    sh "truncate -s 0 ${agentLog}"
                }
            }
        }

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

        stage('test result') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                    script {
                        def testStatus = sh(
                            script: "${cmdPrefix} results ${jobID} | \
                                    awk '{if(/test_status/) print \$2}' | \
                                    tail -1",
                            returnStdout: true).trim().toInteger()

                        echo "Job exit status: ${testStatus}"

                        if (testStatus) {
                            error 'Test (global) FAILED!'
                        } else {
                            echo 'Test (global) PASSED!'
                        }
                    }
                }
            }
        }

        stage('job completion') {
            steps {
                script {
                    try {
                        def compltField = sh(
                            script: "grep -E '${compltRegex}' ${agentLog}",
                            returnStdout: true).trim()

                        // throw prior to echo
                        echo "Job COMPLETE: ${compltField}"
                    } catch (Exception) {
                        echo 'Completion phrase not found!'
                        error 'Job INCOMPLETE!'
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }
    }
}