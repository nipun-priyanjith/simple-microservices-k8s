pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials-id'
        SONAR_HOST_URL = 'http://192.168.88.128:9000'
        SONAR_AUTH_TOKEN = credentials('sonarqube-token-id')
        scannerHome = tool 'Sonar'
        SSH_USER = 'your-ssh-user'
        K8S_HOST = '192.168.88.133'
        K8S_NAMESPACE = 'default'  // Add your Kubernetes namespace if necessary
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
                        
                        // Deploy services
                        SERVICES.each { service ->
                            def image = "nipunxyz/${service}:${BUILD_NUMBER}"
                            def deploymentFile = "k8s/${service}-deployment.yaml"

                            try {
                                sh """
                                    sshpass -p '${PASS}' scp -o StrictHostKeyChecking=no ${deploymentFile} ${USER}@${K8S_HOST}:/home/kube/${service}-deployment.yaml
                                    sshpass -p '${PASS}' ssh -tt -o StrictHostKeyChecking=no ${USER}@${K8S_HOST} '
                                        kubectl apply -f /home/kube/${service}-deployment.yaml -n ${K8S_NAMESPACE} &&
                                        kubectl set image deployment/${service} ${service}=${image} --record -n ${K8S_NAMESPACE} &&
                                        kubectl rollout status deployment/${service} -n ${K8S_NAMESPACE}
                                    '
                                """
                            } catch (Exception e) {
                                error "Deployment of ${service} failed: ${e.message}"
                            }
                        }

                        // Install Helm (optional, if not already installed)
                        try {
                            sh """
                                sshpass -p '${PASS}' ssh -tt -o StrictHostKeyChecking=no ${USER}@${K8S_HOST} 'mkdir -p /home/kube/scripts'
                                sshpass -p '${PASS}' scp -o StrictHostKeyChecking=no scripts/install-helm.sh ${USER}@${K8S_HOST}:/home/kube/scripts/install-helm.sh
                                sshpass -p '${PASS}' ssh -tt -o StrictHostKeyChecking=no ${USER}@${K8S_HOST} << EOF
                                    chmod +x /home/kube/scripts/install-helm.sh
                                    /home/kube/scripts/install-helm.sh
                                EOF
                            """
                        } catch (Exception e) {
                            error "Helm installation failed: ${e.getMessage()}"
                        }

                        // 🛠 Install Ingress Controller using Helm
                        try {
                            sh """
                                sshpass -p '${PASS}' scp -o StrictHostKeyChecking=no scripts/install-ingress-helm.sh ${USER}@${K8S_HOST}:/home/kube/scripts/install-ingress-helm.sh
                                sshpass -p '${PASS}' ssh -tt -o StrictHostKeyChecking=no ${USER}@${K8S_HOST} << EOF
                                    chmod +x /home/kube/scripts/install-ingress-helm.sh
                                    /home/kube/scripts/install-ingress-helm.sh
                                EOF
                            """
                        } catch (Exception e) {
                            error "Ingress controller installation failed: ${e.getMessage()}"
                        }

                        // 🚀 Apply Ingress YAML
                        try {
                            sh """
                                sshpass -p '${PASS}' scp -o StrictHostKeyChecking=no k8s/ingress.yaml ${USER}@${K8S_HOST}:/home/kube/ingress.yaml
                                sshpass -p '${PASS}' ssh -tt -o StrictHostKeyChecking=no ${USER}@${K8S_HOST} '
                                    kubectl apply -f /home/kube/ingress.yaml -n ${K8S_NAMESPACE}
                                '
                            """
                        } catch (Exception e) {
                            error "Ingress deployment failed: ${e.message}"
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            // Clean up docker login after all stages
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
