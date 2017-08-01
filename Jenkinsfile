pipeline {
	agent {label 'slave-w-docker-cromwell-60GB-ebs'}
		
	environment {
		QUAY_PASS = credentials('ottojolanki-quay')
		}
	stages {
		stage('Build') {
			steps {
				echo "$env.BRANCH_NAME"
				sh "docker login -u=ottojolanki -p=${QUAY_PASS} quay.io"
				sh "docker build --no-cache -t filter images/filter/"
				sh "docker tag filter quay.io/ottojolanki/filter:${env.BRANCH_NAME}"
				sh "docker push quay.io/ottojolanki/filter:${env.BRANCH_NAME}"
				sh "docker logout"	
			}
		}
	}
}
