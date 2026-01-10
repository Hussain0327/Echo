"""
Notification handlers for Prefect flow failures and alerts.

This module provides notification capabilities for pipeline monitoring:
- Slack webhook integration
- Email notifications (optional)
- Structured error logging

Usage:
    @flow(on_failure=[notify_on_failure])
    def my_flow():
        ...
"""

import os
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def notify_on_failure(flow: Any, flow_run: Any, state: Any) -> None:
    """
    Handler for flow failure notifications.

    Called automatically by Prefect when a flow fails.
    Sends notifications to configured channels (Slack, email, logs).

    Args:
        flow: The Prefect flow object
        flow_run: The flow run object with run details
        state: The final state of the flow run
    """
    flow_name = flow.name if hasattr(flow, 'name') else str(flow)
    run_id = str(flow_run.id) if hasattr(flow_run, 'id') else 'unknown'
    state_name = state.name if hasattr(state, 'name') else str(state)

    error_message = _extract_error_message(state)

    # Always log the failure
    logger.error(
        "flow_failed",
        flow_name=flow_name,
        run_id=run_id,
        state=state_name,
        error=error_message,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Send Slack notification if configured
    slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if slack_webhook_url:
        _send_slack_notification(
            webhook_url=slack_webhook_url,
            flow_name=flow_name,
            run_id=run_id,
            state=state_name,
            error=error_message,
        )

    # Send email notification if configured
    email_recipients = os.getenv("ALERT_EMAIL_RECIPIENTS")
    if email_recipients:
        _send_email_notification(
            recipients=email_recipients.split(","),
            flow_name=flow_name,
            run_id=run_id,
            state=state_name,
            error=error_message,
        )


def notify_on_completion(flow: Any, flow_run: Any, state: Any) -> None:
    """
    Handler for flow completion notifications (optional).

    Can be used to track successful pipeline runs.
    """
    flow_name = flow.name if hasattr(flow, 'name') else str(flow)
    run_id = str(flow_run.id) if hasattr(flow_run, 'id') else 'unknown'

    logger.info(
        "flow_completed",
        flow_name=flow_name,
        run_id=run_id,
        state="COMPLETED",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _extract_error_message(state: Any) -> str:
    """Extract error message from flow state."""
    try:
        if hasattr(state, 'message'):
            return str(state.message)
        if hasattr(state, 'result'):
            result = state.result()
            if isinstance(result, Exception):
                return str(result)
        return "Unknown error"
    except Exception:
        return "Error extracting failure details"


def _send_slack_notification(
    webhook_url: str,
    flow_name: str,
    run_id: str,
    state: str,
    error: str,
) -> None:
    """Send notification to Slack webhook."""
    try:
        import httpx

        message = {
            "text": f":x: Pipeline Failed: *{flow_name}*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Pipeline Failure: {flow_name}",
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Flow:*\n{flow_name}"},
                        {"type": "mrkdwn", "text": f"*Run ID:*\n{run_id[:8]}..."},
                        {"type": "mrkdwn", "text": f"*State:*\n{state}"},
                        {"type": "mrkdwn", "text": f"*Time:*\n{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"},
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error:*\n```{error[:500]}```"
                    }
                }
            ]
        }

        response = httpx.post(webhook_url, json=message, timeout=10.0)
        response.raise_for_status()
        logger.info("slack_notification_sent", flow_name=flow_name)

    except Exception as e:
        logger.warning("slack_notification_failed", error=str(e))


def _send_email_notification(
    recipients: list[str],
    flow_name: str,
    run_id: str,
    state: str,
    error: str,
) -> None:
    """Send email notification (placeholder for SMTP integration)."""
    # This is a placeholder - implement with your preferred email service
    # Options: AWS SES, SendGrid, SMTP, etc.
    logger.info(
        "email_notification_would_send",
        recipients=recipients,
        flow_name=flow_name,
        subject=f"Pipeline Failed: {flow_name}",
    )
