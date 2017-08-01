pipeline {
	agent { 
		node {
		label 'slave-w-docker-cromwell-60GB-ebs'
		git url: 'https://github.com/ottojolanki/pipeline-container.git'
		sh "git rev-parse --abbrev-ref HEAD > GIT_BRANCH"
		GIT_BRANCH = readFile('GIT_BRANCH').trim() 
		}
	}	
	environment {
		QUAY_PASS = credentials('ottojolanki-quay')
		}
	stages {
		stage('Build') {
			steps {
				echo "Building.. ${GIT_BRANCH}"
				sh "docker login -u=ottojolanki -p=${QUAY_PASS} quay.io"
				sh "docker logout"	
			}
		}
	}
}
