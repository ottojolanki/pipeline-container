pipeline {
	agent {label 'slave-w-docker-cromwell-60GB-ebs'}
		
	environment {
		QUAY_PASS = credentials('ottojolanki-quay')
		}
	stages {
		stage('Unit tests') {
			steps {
				echo 'Running unit tests..'			
				sh 'python tests/unit_tests.py'
			}
		}
		stage('Build-nonmaster') {
			when { not { branch 'master' } }
			steps {
				echo "$env.BRANCH_NAME"
				echo "Running non-master build steps."
				sh "docker login -u=ottojolanki -p=${QUAY_PASS} quay.io"
				sh "docker build --no-cache -t filter images/filter/"
				sh "docker tag filter quay.io/ottojolanki/filter:${env.BRANCH_NAME}"
				sh "docker push quay.io/ottojolanki/filter:${env.BRANCH_NAME}"
				sh "docker logout"	
			}
		}
		stage('Build-master') {
			when { branch 'master'}
			steps {
				echo env.BRANCH_NAME
				echo "Running master build steps."
			}
		}		 
	}
	post {
		success {
			echo 'Post build actions that run on success'
		}
		failure {
			echo 'Post build actions that run on failure'
		}
		always {
			echo 'Post build actions that run always'
		} 
	}
}
