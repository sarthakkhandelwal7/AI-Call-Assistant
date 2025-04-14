# Deployment Guide: AI Call Assistant on AWS

This guide details the steps to deploy the full AI Call Assistant application (backend, frontend, infrastructure) to AWS using Terraform, Docker, AWS ECR, App Runner, S3, and CloudFront.

## 1. Prerequisites

-   **AWS Account:** An active AWS account with necessary permissions to create VPC, RDS, ECR, App Runner, S3, CloudFront, Secrets Manager, and IAM resources.
-   **AWS CLI:** Configured with credentials for your AWS account (`aws configure`).
-   **Terraform:** Installed locally (>= v1.0).
-   **Docker:** Installed locally and running.
-   **Git:** To clone the repository.
-   **Google Cloud Project:** A project set up with OAuth 2.0 credentials (Client ID and Client Secret) for Google Login.
-   **Project Code:** Clone the AI Call Assistant repository.

## 2. Project Structure Overview

-   `backend/`: Contains the FastAPI backend application code and its Dockerfile.
-   `frontend/`: Contains the React frontend application code and its Dockerfile (used for building).
-   `terraform/`: Contains all Terraform configuration files for managing AWS infrastructure.

## 3. Infrastructure Setup (Terraform)

The `terraform/` directory contains the Infrastructure as Code (IaC) definitions.

**Terraform Files & Purpose:**

-   `providers.tf`: Configures the AWS provider.
-   `variables.tf`: Defines input variables (like project name, environment, region).
-   `outputs.tf`: Defines outputs after deployment (like App Runner URL, S3 bucket name, CloudFront domain).
-   `vpc.tf`: Defines the Virtual Private Cloud (VPC), subnets (public/private), Internet Gateway, NAT Gateway, and route tables. This creates the network foundation.
-   `rds.tf`: Defines the AWS RDS PostgreSQL database instance, parameter group, and subnet group. Places the database in private subnets.
-   `ecr.tf`: Defines the Elastic Container Registry (ECR) repository to store the backend Docker image.
-   `secrets.tf`: Defines AWS Secrets Manager secrets to store sensitive information like database credentials, API keys (OpenAI, Twilio), Google OAuth secrets, and JWT secret. This avoids hardcoding secrets in code or Terraform state.
-   `iam.tf`: Defines necessary IAM roles and policies for App Runner:
    -   **Access Role:** Allows App Runner to pull images from ECR during deployment.
    -   **Instance Role:** Allows the running App Runner container to access other AWS services, specifically Secrets Manager.
-   `apprunner.tf`: Defines the AWS App Runner service for the backend:
    -   Configures the source from the ECR image.
    -   Injects environment variables and secrets into the running container. Secrets are referenced securely from Secrets Manager using the Instance Role. Non-secret variables like `DATABASE_URL` and `FRONTEND_URL` are constructed dynamically using other Terraform resource outputs.
    -   Sets up network configuration to connect to the VPC (for RDS access).
    -   Configures instance size (CPU/Memory).
-   `s3_cloudfront.tf`: Defines:
    -   An S3 bucket to host the static frontend assets (React build output).
    -   A CloudFront distribution to act as a CDN for the S3 bucket, providing HTTPS and caching.
    -   Origin Access Control (OAC) to ensure the S3 bucket is only accessible via CloudFront.
-   `security_groups.tf` (Implied/Included in others): Defines security groups to control traffic flow (e.g., allowing App Runner to reach RDS, allowing public access to CloudFront).

**Deployment Steps:**

1.  **Configure AWS CLI:** Ensure your AWS CLI is configured with access keys that have sufficient permissions.
    ```bash
    aws configure
    ```
2.  **Initialize Terraform:** Navigate to the terraform directory.
    ```bash
    cd /path/to/AI-Call-Assistant/terraform
    terraform init
    ```
3.  **Apply Terraform Configuration:** This creates the AWS resources, including the secret containers.

    ```bash
    terraform apply
    ```

    Confirm with `yes` when prompted. Wait for completion.

4.  **Populate Secrets in AWS Secrets Manager:** Terraform created the secrets but used placeholders. You must now add the real values:

    -   Go to the AWS Secrets Manager console in the correct region.
    -   Find the secrets created by Terraform (names will be like `ai-call-assistant-app-secrets-dev` and `ai-call-assistant-db-credentials-dev`, adjust based on your `var.project_name` and `var.environment`).
    -   For the **Application Secrets** (`...-app-secrets-...`):
        -   Click "Retrieve secret value".
        -   Click "Edit".
        -   Replace the placeholder values for the following keys with your actual secrets:
            -   `OPENAI_API_KEY`
            -   `TWILIO_ACCOUNT_SID`
            -   `TWILIO_AUTH_TOKEN`
            -   `TWILIO_VERIFY_SERVICE_SID`
            -   `GOOGLE_CLIENT_ID`
            -   `GOOGLE_CLIENT_SECRET`
            -   `JWT_SECRET_KEY` (Use a strong random string)
        -   Click "Save".
    -   For the **Database Credentials** (`...-db-credentials-...`):
        -   Terraform likely populated this with the initially generated RDS master password. Verify the `username` and `password` are correct or update if necessary (though usually App Runner reads what Terraform stored).

5.  **Note Terraform Outputs:** Useful values for subsequent steps.
    ```bash
    terraform output
    ```
    Note `apprunner_backend_service_url`, `frontend_bucket_name`, `frontend_distribution_id`, `frontend_distribution_domain_name`, `backend_ecr_repo_name`.

## 4. Backend Deployment (App Runner)

The backend is a FastAPI application containerized using Docker.

**Deployment Steps:**

1.  **Build Backend Docker Image:** Navigate to the project root directory. Using Docker Compose (recommended, reads image name from `docker-compose.dev.yml`):

    ```bash
    cd /path/to/AI-Call-Assistant
    # Ensure docker-compose.dev.yml specifies the correct ECR image name format
    docker-compose -f docker-compose.dev.yml build backend
    ```

    _Alternatively, using manual build and tag:_

    ```bash
    # cd /path/to/AI-Call-Assistant
    # AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    # AWS_REGION=$(aws configure get region)
    # ECR_REPO_NAME=$(terraform -chdir=terraform output -raw backend_ecr_repo_name)
    # ECR_IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:v1.0.0"
    # docker build -t $ECR_IMAGE_URI -f backend/Dockerfile ./backend
    ```

    _(Ensure the tag `v1.0.0` matches `apprunner.tf`)_

2.  **Push Image to ECR:**

    ```bash
    AWS_REGION=$(aws configure get region) # Or set your deployment region
    ECR_IMAGE_URI=$(docker inspect --format='{{index .RepoDigests 0}}' ai-call-assistant-backend | cut -d'@' -f1) # Get from compose build if used
    # If compose not used, use the ECR_IMAGE_URI from alternative build step above

    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(echo $ECR_IMAGE_URI | cut -d'/' -f1)
    docker push $ECR_IMAGE_URI # Pushes the image built by compose or manually
    ```

3.  **Run Database Migrations:** The backend application needs its database schema initialized. App Runner doesn't run migrations automatically. You need to run them manually against the RDS instance _once_ after it's created.
    -   **Get Database URL:** Construct the `DATABASE_URL` using the RDS endpoint and the credentials stored in Secrets Manager. You can get the endpoint from Terraform output (`terraform -chdir=terraform output -raw db_instance_endpoint`) or the AWS console.
        ```
        postgresql+asyncpg://<db_user>:<db_password>@<rds_endpoint>/<db_name>
        ```
    -   **Set Environment Variable:** Export the `DATABASE_URL` in your local terminal (ensure you have network access to the RDS instance - this might require temporary security group changes, a bastion host, or running from an EC2 instance in the VPC).
        ```bash
        export DATABASE_URL="postgresql+asyncpg://<user>:<password>@<endpoint>/<db_name>"
        # Also export other required env vars needed by Alembic/FastAPI config locally
        export OPENAI_API_KEY="..."
        export TWILIO_ACCOUNT_SID="..."
        # ... (and others defined in backend/app/core/config.py, except STREAM_URL)
        ```
    -   **Run Migrations:** Navigate to the backend directory and run Alembic.
        ```bash
        cd backend
        alembic upgrade head
        cd .. # Return to project root
        ```
4.  **Trigger App Runner Deployment:** Since `auto_deployments_enabled = false`, manually start the deployment.
    -   **Using AWS CLI (Recommended):**
        ```bash
        APPRUNNER_SERVICE_ARN=$(terraform -chdir=terraform output -raw apprunner_backend_service_arn)
        aws apprunner start-deployment --service-arn $APPRUNNER_SERVICE_ARN
        ```
    -   **Using AWS Console:** Go to the AWS App Runner console, select your service, and manually trigger a deployment using the "Deploy" button.
5.  **Verify Backend Health:** Monitor the App Runner deployment. Once it shows "Running", check the logs for any errors. The `STREAM_URL` validation error should now be gone because we removed it from `config.py` and generate it dynamically in `call_routes.py`.

## 5. Frontend Deployment (S3/CloudFront)

The frontend is a React application. We use Docker only for the _build process_ to create static assets.

**Deployment Steps:**

1.  **Set Build-Time Environment Variables:** Navigate to the project root directory. These need to be available in your shell when running `docker build`.
    -   **Backend API URL:** Get the App Runner URL from Terraform output.
        ```bash
        # Ensure you are in the project root directory (AI-Call-Assistant)
        export BACKEND_API_URL="https://$(terraform -chdir=terraform output -raw apprunner_backend_service_url)"
        echo $BACKEND_API_URL # Verify it's set correctly
        ```
    -   **Google Client ID:** Get this from your Google Cloud Project credentials.
        ```bash
        export GOOGLE_CLIENT_ID="<your_google_client_id>"
        echo $GOOGLE_CLIENT_ID # Verify it's set correctly
        ```
2.  **Build Frontend Docker Image (for Build Artifacts):** This passes the environment variables as build arguments.
    ```bash
    # Ensure you are in the project root directory
    docker build \
      --build-arg REACT_APP_API_URL="$BACKEND_API_URL" \
      --build-arg REACT_APP_GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
      -t frontend-app-build \
      -f frontend/Dockerfile \
      ./frontend
    ```
    _(Note: We addressed an earlier issue where `AuthContext.js` had hardcoded `localhost:8000`. This was fixed by refactoring it to use functions from `services/api.js`, which correctly reads `process.env.REACT_APP_API_URL` passed via the build arg.)_
3.  **Copy Build Artifacts:** Extract the static files (`/app/build` inside the container) to a local directory.
    ```bash
    # Ensure you are in the project root directory
    rm -rf build_output # Remove previous output
    docker create --name temp_frontend_build frontend-app-build
    docker cp temp_frontend_build:/app/build ./build_output
    docker rm temp_frontend_build # Clean up container
    ```
4.  **Sync Assets to S3:** Upload the contents of `build_output` to the S3 bucket created by Terraform.
    ```bash
    # Get bucket name from terraform output
    S3_BUCKET_NAME=$(terraform -chdir=terraform output -raw frontend_bucket_name)
    aws s3 sync ./build_output s3://${S3_BUCKET_NAME} --delete
    ```
5.  **Invalidate CloudFront Cache:** Tell CloudFront to fetch the latest files from S3.
    ```bash
    # Get distribution ID from terraform output
    CLOUDFRONT_DIST_ID=$(terraform -chdir=terraform output -raw frontend_distribution_id)
    aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_DIST_ID} --paths "/*"
    ```

## 6. Verification

1.  **Access Frontend:** Open your CloudFront domain name (from Terraform output `frontend_distribution_domain_name`) in a browser: `https://<your_cloudfront_domain>`.
2.  **Test Login:** Attempt the Google Login flow.
3.  **Check Network Calls:** Use your browser's developer tools (Network tab) to inspect the API calls. Verify they are going to your `BACKEND_API_URL` (App Runner URL) and not `localhost`.
4.  **Check Backend Logs:** Monitor App Runner logs for any errors during login or other API interactions.
5.  **Test Call Flow (Optional but Recommended):** If you have configured a Twilio number, try calling it to test the inbound call flow and WebSocket connection.

## 7. Conclusion

Following these steps deploys the AI Call Assistant with a scalable backend on App Runner, a globally distributed frontend via CloudFront/S3, and a secure database on RDS. Infrastructure is managed via Terraform, and secrets are handled securely using AWS Secrets Manager. The key challenges related to environment variable injection (especially build-time vs. runtime), CORS, database migrations, and dynamic URL generation have been addressed.
