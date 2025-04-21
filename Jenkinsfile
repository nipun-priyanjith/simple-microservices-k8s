pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials-id'
        SONAR_HOST_URL = 'http://192.168.88.128:9000'
        SONAR_AUTH_TOKEN = credentials('sonarqube-token-id')
        scannerHome = tool 'Sonar'
        SSH_USER = 'your-ssh-user'
        K8S_HOST = '192.168.88.133'
        // Removed PROJECT_DIR since it's not needed
    }

    stages {
        stage('Clone Repository') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/nipun-priyanjith/simple-microservices-k8s.git'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    def SERVICES = ['api-gateway', 'user-service', 'product-service']
                    SERVICES.each { service ->
                        dir("${service}") {
                            withSonarQubeEnv('Sonar') {
                                sh """
                                    ${scannerHome}/bin/sonar-scanner \
                                    -Dsonar.projectKey=${service} \
                                    -Dsonar.projectName=${service} \
                                    -Dsonar.projectVersion=${BUILD_NUMBER} \
                                    -Dsonar.sources=.
                                """
                            }
                        }
                    }
                }
            }
        }

        stage('Build & Push Docker Images') {
            steps {
                script {
                    def SERVICES = ['api-gateway', 'user-service', 'product-service']
                    withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS_ID}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh "echo '${DOCKER_PASS}' | docker login -u '${DOCKER_USER}' --password-stdin"

                        SERVICES.each { service ->
                            def image = "nipunxyz/${service}:${BUILD_NUMBER}"
                            dir("${service}") {
                                sh "docker build -t ${image} ."
                                sh "docker push ${image}"
                            }
                        }
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    def SERVICES = ['api-gateway', 'user-service', 'product-service']
                    withCredentials([usernamePassword(credentialsId: 'k8s-master-password', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        SERVICES.each { service ->
                            def image = "nipunxyz/${service}:${BUILD_NUMBER}"
                            def deploymentFile = "k8s/${service}-deployment.yaml"

                            sh """
                                sshpass -p '${PASS}' scp -o StrictHostKeyChecking=no ${deploymentFile} ${USER}@${K8S_HOST}:/home/kube/${service}-deployment.yaml
                                sshpass -p '${PASS}' ssh -tt -o StrictHostKeyChecking=no ${USER}@${K8S_HOST} '
                                    kubectl apply -f /home/kube/${service}-deployment.yaml &&
                                    kubectl set image deployment/${service} ${service}=${image} --record &&
                                    kubectl rollout status deployment/${service}
                                '
                            """
                        }

                        sh """
                            sshpass -p '${PASS}' scp -o StrictHostKeyChecking=no k8s/ingress.yaml ${USER}@${K8S_HOST}:/home/kube/ingress.yaml
                            sshpass -p '${PASS}' ssh -tt -o StrictHostKeyChecking=no ${USER}@${K8S_HOST} '
                                kubectl apply -f /home/kube/ingress.yaml
                            '
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            sh "docker logout"
        }
        success {
            echo "✅ All services deployed successfully!"
        }
        failure {
            echo "❌ Deployment failed. Please check logs!"
        }
    }
}
