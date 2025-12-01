# Cloud Deployment Configuration Files

## 1. Dockerfile for Cloud Run (Stateless Agents)

```dockerfile
# Dockerfile for Reviewer and Meta-Reviewer Agents
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY router_agent_orchestrator.py .
COPY agent_a_author.py .
COPY ds_star_agent.py .

# Set environment variables
ENV PORT=8080
ENV GCP_PROJECT_ID=${GCP_PROJECT_ID}

# Run the application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
```

## 2. requirements.txt

```txt
# Core dependencies
google-cloud-firestore==2.13.1
google-cloud-storage==2.10.0
redis==5.0.1
flask==3.0.0
gunicorn==21.2.0

# Vertex AI
google-cloud-aiplatform==1.38.1
vertexai==1.38.0

# LangChain (for Agent Engine)
langchain==0.1.0
langchain-google-vertexai==0.0.6

# Utilities
python-dotenv==1.0.0
pydantic==2.5.0
```

## 3. cloudbuild.yaml (CI/CD)

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/author-agent:$COMMIT_SHA', '.']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/author-agent:$COMMIT_SHA']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'author-agent'
      - '--image'
      - 'gcr.io/$PROJECT_ID/author-agent:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

images:
  - 'gcr.io/$PROJECT_ID/author-agent:$COMMIT_SHA'
```

## 4. terraform/main.tf (Infrastructure as Code)

```hcl
# Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Firestore Database
resource "google_firestore_database" "research_sessions" {
  name        = "research-sessions"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Cloud Storage Bucket
resource "google_storage_bucket" "agent_artifacts" {
  name     = "${var.project_id}-agent-artifacts"
  location = var.region
  
  lifecycle_rule {
    condition {
      age = 90  # Delete after 90 days
    }
    action {
      type = "Delete"
    }
  }
}

# Memorystore (Redis) Instance
resource "google_redis_instance" "cache" {
  name           = "agent-cache"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region
  
  redis_version = "REDIS_6_X"
}

# Cloud Run Service (Author Agent)
resource "google_cloud_run_service" "author_agent" {
  name     = "author-agent"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/author-agent:latest"
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "REDIS_HOST"
          value = google_redis_instance.cache.host
        }
        
        env {
          name  = "GCS_BUCKET"
          value = google_storage_bucket.agent_artifacts.name
        }
      }
    }
  }
}

# IAM Policy for Cloud Run
resource "google_cloud_run_service_iam_member" "author_agent_public" {
  service  = google_cloud_run_service.author_agent.name
  location = google_cloud_run_service.author_agent.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}
```

## 5. deploy.sh (Deployment Script)

```bash
#!/bin/bash
set -e

# Configuration
PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="author-agent"

echo "🚀 Deploying Author Agent with Memory to Google Cloud"
echo "=================================================="

# 1. Set project
echo "Setting GCP project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# 2. Enable required APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable aiplatform.googleapis.com

# 3. Create Firestore database (if not exists)
echo "Creating Firestore database..."
gcloud firestore databases create --region=$REGION || true

# 4. Create Cloud Storage bucket
echo "Creating Cloud Storage bucket..."
gsutil mb -l $REGION gs://$PROJECT_ID-agent-artifacts || true

# 5. Deploy Redis instance
echo "Deploying Memorystore (Redis) instance..."
gcloud redis instances create agent-cache \
    --size=1 \
    --region=$REGION \
    --redis-version=redis_6_x \
    --tier=basic || true

# 6. Get Redis host
REDIS_HOST=$(gcloud redis instances describe agent-cache --region=$REGION --format="value(host)")
echo "Redis host: $REDIS_HOST"

# 7. Build and deploy to Cloud Run
echo "Building and deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,REDIS_HOST=$REDIS_HOST,GCS_BUCKET=$PROJECT_ID-agent-artifacts" \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300

# 8. Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo "✅ Deployment complete!"
echo "=================================================="
echo "Service URL: $SERVICE_URL"
echo "Redis Host: $REDIS_HOST"
echo "Storage Bucket: gs://$PROJECT_ID-agent-artifacts"
echo "=================================================="
```

## 6. main.py (Flask API for Cloud Run)

```python
"""
Flask API for Author Agent Cloud Run deployment
"""
from flask import Flask, request, jsonify
from agent_a_cloud_deployment import AuthorAgentWithMemory
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

@app.route('/generate', methods=['POST'])
def generate_document():
    """
    Generate research document endpoint.
    
    Request body:
    {
        "session_id": "optional-session-id",
        "research_topic": "Mobile App Retention",
        "previous_kill_list": ""
    }
    """
    try:
        data = request.json
        
        # Initialize agent
        agent = AuthorAgentWithMemory(
            session_id=data.get("session_id"),
            research_topic=data.get("research_topic")
        )
        
        # Generate document
        document = agent.invoke(
            prompt=data.get("prompt", "Generate research document"),
            context={"PREVIOUS_KILL_LIST": data.get("previous_kill_list", "")}
        )
        
        return jsonify({
            "success": True,
            "session_id": agent.session_id,
            "document": document,
            "iteration": agent.iteration_count
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information."""
    try:
        from agent_a_cloud_deployment import SessionManager
        sessions = SessionManager()
        session_data = sessions.get_session(session_id)
        
        if session_data:
            return jsonify({
                "success": True,
                "session": session_data
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

## Deployment Commands

### Quick Deploy (Cloud Run)
```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Deploy with Terraform
```bash
cd terraform
terraform init
terraform plan -var="project_id=your-project-id"
terraform apply -var="project_id=your-project-id"
```

### Test Deployment
```bash
# Test health endpoint
curl https://author-agent-XXXXX-uc.a.run.app/health

# Test document generation
curl -X POST https://author-agent-XXXXX-uc.a.run.app/generate \
  -H "Content-Type: application/json" \
  -d '{
    "research_topic": "Mobile App Retention Using AI",
    "previous_kill_list": ""
  }'
```
