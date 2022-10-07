def yamlFile = 
    '''
    job_queue: makrutlime
    provision_data:
      distro: focal
    test_data:
      test_cmds: |-
        ifconfig
    '''

pipeline {
    agent { label 'makrutlime' }

    stages {
        stage('Write yaml') {
            steps {
                script {
                    if (fileExists('/home/jenkins/job.yaml')) {
                        echo "job.yaml exists; overwriting"
                        sh 'rm /home/jenkins/job.yaml'

                    }

                    writeFile file: "/home/jenkins/job.yaml", text: yamlFile
                }
            }
        }
        stage('Run Testflinger') {
            steps {
                script {
                    sh 'testflinger-cli --server http://10.245.128.10:8000 submit -q /home/jenkins/job.yaml > jobID'
                    jobID = readFile 'jobID'
                    echo 'JOB ID: ${jobID}'
                    sh 'testflinger-cli poll ${jobID} > pollStatus'
                    pollStatus = readFile 'pollStatus'
                    echo 'Poll Status: pollStatus'
                }
            }
        }
    }
}
