pipeline {
    agent any

    environment {
        IMAGE_TAG = "${BUILD_NUMBER}"
        DOCKERHUB_USER = 'nipunxyz'
    }

    stages {
        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        stage('Clone Repository') {
            steps {
                echo "✅ Cloning Repository..."
                sh 'git clone https://github.com/nipunxyz/multi-k8s-project.git'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                echo "🔍 Running SonarQube Analysis..."
                // Add your SonarQube analysis command here if needed
            }
        }

        stage('Build & Push Docker Images') {
            steps {
                script {
                    def services = ['api-gateway', 'user-service', 'product-service']
                    for (svc in services) {
                        sh """
                            echo "🐳 Building Docker image for ${svc}"
                            docker build -t ${DOCKERHUB_USER}/${svc}:${IMAGE_TAG} ./${svc}
                            echo "🚀 Pushing Docker image for ${svc}"
                            docker push ${DOCKERHUB_USER}/${svc}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'k8s-master-password', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    script {
                        def services = ['api-gateway', 'user-service', 'product-service']

                        for (svc in services) {
                            sh '''#!/bin/bash
                                sshpass -p "$PASS" scp -o StrictHostKeyChecking=no k8s/${svc}-deployment.yaml $USER@192.168.88.133:/home/kube/${svc}-deployment.yaml
                                sshpass -p "$PASS" ssh -tt -o StrictHostKeyChecking=no $USER@192.168.88.133 <<EOF
                                    kubectl apply -f /home/kube/${svc}-deployment.yaml -n default
                                    kubectl set image deployment/${svc} ${svc}=${DOCKERHUB_USER}/${svc}:${IMAGE_TAG} --record -n default
                                    kubectl rollout status deployment/${svc} -n default
EOF
                            '''
                        }

                        // Install ingress controller script
                        sh '''#!/bin/bash
                            sshpass -p "$PASS" scp -o StrictHostKeyChecking=no scripts/install-ingress-helm.sh $USER@192.168.88.133:/home/kube/scripts/install-ingress-helm.sh
                            sshpass -p "$PASS" ssh -tt -o StrictHostKeyChecking=no $USER@192.168.88.133 <<EOF
                                export PATH=$PATH:/usr/local/bin
                                chmod +x /home/kube/scripts/install-ingress-helm.sh
                                /home/kube/scripts/install-ingress-helm.sh
EOF
                        '''

                        // Deploy ingress.yaml with webhook readiness checks
                        sh '''#!/bin/bash
                            sshpass -p "$PASS" scp -o StrictHostKeyChecking=no k8s/ingress.yaml $USER@192.168.88.133:/home/kube/ingress.yaml
                            sshpass -p "$PASS" ssh -tt -o StrictHostKeyChecking=no $USER@192.168.88.133 <<EOF
                                echo "🔄 Waiting for ingress webhook service and endpoint to be ready..."
                                for i in {1..12}; do
                                    kubectl get svc ingress-nginx-controller-admission -n ingress-nginx >/dev/null 2>&1 && break
                                    echo "⏳ Waiting for webhook service... retrying in 5s"
                                    sleep 5
                                done

                                echo "✅ Webhook service found."

                                echo "⏳ Waiting for webhook endpoints to be ready..."
                                for i in {1..12}; do
                                    READY_ENDPOINTS=$(kubectl get endpoints ingress-nginx-controller-admission -n ingress-nginx -o jsonpath="{.subsets[*].addresses[*].ip}")
                                    if [ ! -z "$READY_ENDPOINTS" ]; then
                                        echo "✅ Webhook endpoint ready: $READY_ENDPOINTS"
                                        break
                                    fi
                                    echo "⏳ Endpoint not ready, waiting 5s..."
                                    sleep 5
                                done

                                echo "⏳ Waiting for ingress controller pod to be ready..."
                                kubectl wait --namespace ingress-nginx \
                                  --for=condition=Ready pod \
                                  --selector=app.kubernetes.io/component=controller \
                                  --timeout=120s

                                echo "🚀 Applying ingress.yaml now..."
                                kubectl apply -f /home/kube/ingress.yaml -n default
EOF
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            echo '✅ Deployment Completed Successfully!'
        }
        failure {
            echo '❌ Deployment Failed. Please check the logs.'
        }
    }
}
