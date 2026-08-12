# AI Code Generation System

A portfolio-ready web application that converts GitHub issues into Python code with Generative AI.

## Demo
The app includes a **Demo mode** so it can be shown without AWS credentials. It provides sample GitHub issues and demonstrates the generation workflow.

## Production architecture
GitHub API → Streamlit/Python → Amazon Bedrock (Claude) → generated Python code → optional Amazon S3 storage.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit. Demo mode is enabled by default.

## GitHub integration
Set `GITHUB_TOKEN` and `GITHUB_REPO` as environment variables, then turn off Demo mode.

## AWS / Bedrock
Set `AWS_REGION` and `BEDROCK_MODEL_ID`, configure AWS credentials/role, and turn off Demo mode. Bedrock model availability depends on your AWS account and region.

## Security
Never commit GitHub tokens, AWS access keys, `.env` files, or other secrets. Use environment variables, IAM roles, or AWS Secrets Manager.

## Features

- Converts GitHub issues into Python code using Generative AI
- Integrates with GitHub API
- Uses Amazon Bedrock with Claude
- Includes Demo mode without AWS credentials
- Streamlit-based web application
- Optional Amazon S3 storage

## Tech Stack

- Python
- Streamlit
- GitHub API
- Amazon Bedrock
- Claude
- AWS S3
- Generative AI
