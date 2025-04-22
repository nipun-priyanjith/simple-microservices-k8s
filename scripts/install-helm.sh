#!/bin/bash

echo "📦 Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
helm version
