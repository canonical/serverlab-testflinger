pipeline {
    agent { label 'kies' }

    stages {
        stage('execute test') {
            steps {
                echo 'Executing tf test'
                sh """
                    set +e
                    cat > job.yaml <<EOF
                    job_queue: kies
                    provision_data:
                      distro: focal
                    test_data:
                      test_cmds: |
                        ifconfig
                    EOF
                    JOB_ID=\$(testflinger-cli submit -q job.yaml)
                    echo "JOB_ID: \${JOB_ID}"
                    testflinger-cli poll \${JOB_ID}
                    testflinger-cli artifacts \${JOB_ID}
                    tar -xzf artifacts.tgz
                    TEST_STATUS=\$(testflinger-cli results \${{JOB_ID}} |jq -r .test_status)
                    echo "Test exit status: \${TEST_STATUS}"
                """
            }
        }
    }
}