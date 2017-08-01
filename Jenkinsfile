pipeline {
	agent { label 'slave-w-docker-cromwell-60GB-ebs' }
	environment {
		QUAY_PASS = credentials('ottojolanki-quay')
		BRANCH = sh (
			script: "echo ${GIT_BRANCH} | sed 's/origin\///'"
			)
		}
	stages {
		stage('Build') {
			steps {
				echo 'Building..'
				sh "docker login -u=ottojolanki -p=${QUAY_PASS} quay.io"
				sh "docker logout"	
			}
		}
	}
}
