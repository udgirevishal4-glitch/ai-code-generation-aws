"""AI-powered code generation from GitHub issues using Amazon Bedrock.

AWS Lambda entry point: lambda_handler
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

GITHUB_API = "https://api.github.com"
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0"
)
DEFAULT_LANGUAGE = os.getenv("LANGUAGE", "python")

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))
MAX_ISSUES = int(os.getenv("MAX_ISSUES", "10"))


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def github_headers() -> Dict[str, str]:
    token = required_env("GITHUB_PAT")
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_open_issues(owner: str, repo: str) -> List[Dict[str, Any]]:
    """Fetch open GitHub issues, excluding pull requests."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    response = requests.get(
        url,
        headers=github_headers(),
        params={"state": "open", "per_page": min(MAX_ISSUES, 100)},
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()

    # GitHub returns pull requests through the issues endpoint too.
    return [item for item in response.json() if "pull_request" not in item]


def invoke_bedrock(prompt: str) -> str:
    """Send a prompt to Claude through Amazon Bedrock."""
    bedrock = boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    }

    try:
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body),
            accept="application/json",
            contentType="application/json",
        )
        model_response = json.loads(response["body"].read())
        return model_response["content"][0]["text"]
    except (ClientError, BotoCoreError, KeyError, json.JSONDecodeError) as exc:
        LOGGER.exception("Amazon Bedrock invocation failed")
        raise RuntimeError("Amazon Bedrock invocation failed") from exc


def design_agent(issue: str, message: str, language: str) -> str:
    """Create a concise technical design for a GitHub issue."""
    prompt = f"""
You are a senior software architect.
Create a concise implementation design for this GitHub issue.

Issue: {issue}
Description: {message or "No description provided."}
Target language: {language}

Return:
1. Requirements
2. Proposed approach
3. Main components/functions
4. Important edge cases
5. Testing considerations
"""
    return invoke_bedrock(prompt)


def code_generation_agent(issue: str, message: str, language: str, design: str = "") -> str:
    """Generate production-oriented source code from an issue and design."""
    prompt = f"""
You are an expert software developer.
Generate production-ready {language} code for the GitHub issue below.

Issue: {issue}
Description: {message or "No description provided."}
Technical design:
{design or "Create a sensible design before implementing."}

Requirements:
- Return only source code, with no Markdown fences or explanation.
- Use clear naming and useful comments only where needed.
- Handle reasonable errors and edge cases.
- Keep the implementation focused on the issue.
"""
    return invoke_bedrock(prompt)


def clean_code_response(code: str) -> str:
    """Remove accidental Markdown code fences from model output."""
    cleaned = code.strip()
    cleaned = re.sub(r"^```(?:python|py|java|javascript|js|[a-zA-Z0-9_+-]+)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip() + "\n"


def save_code_s3_bucket(code: str, s3_bucket: str, key: str) -> None:
    """Store generated source code in Amazon S3."""
    s3 = boto3.client("s3", region_name=AWS_REGION)
    try:
        s3.put_object(
            Bucket=s3_bucket,
            Key=key,
            Body=code.encode("utf-8"),
            ContentType="text/plain; charset=utf-8",
        )
        LOGGER.info("Generated code saved to s3://%s/%s", s3_bucket, key)
    except (ClientError, BotoCoreError) as exc:
        LOGGER.exception("Failed to save generated code to S3")
        raise RuntimeError("Failed to save generated code to S3") from exc


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entry point."""
    owner = required_env("GITHUB_OWNER")
    repo = required_env("GITHUB_REPO")
    s3_bucket = required_env("S3_BUCKET")
    language = os.getenv("LANGUAGE", DEFAULT_LANGUAGE)

    issues = get_open_issues(owner, repo)
    results = []

    for issue in issues[:MAX_ISSUES]:
        number = issue["number"]
        title = issue.get("title", "Untitled issue")
        message = issue.get("body") or ""
        LOGGER.info("Processing GitHub issue #%s: %s", number, title)

        design = design_agent(title, message, language)
        generated_code = clean_code_response(
            code_generation_agent(title, message, language, design)
        )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        key = f"generated/{language}/issue-{number}/{timestamp}.txt"
        save_code_s3_bucket(generated_code, s3_bucket, key)

        results.append({
            "issue": number,
            "title": title,
            "s3_key": key,
        })

    return {
        "statusCode": 200,
        "body": json.dumps({"processed_issues": results}),
    }
