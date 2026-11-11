import logging
import math
import random
import re
import time

from google.genai.errors import APIError


logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 3
MAX_RATE_LIMIT_WAIT_SECONDS = 30


class GeminiRequestError(RuntimeError):
    def __init__(self, message, retryable=False, retry_after_seconds=0):
        super().__init__(message)
        self.retryable = retryable
        self.retry_after_seconds = retry_after_seconds


def _error_details(error):
    details = getattr(error, "details", None)
    if not isinstance(details, dict):
        return {}, []
    body = details.get("error", details)
    if not isinstance(body, dict):
        return {}, []
    violations = []
    for detail in body.get("details", []):
        if isinstance(detail, dict) and detail.get("@type", "").endswith("QuotaFailure"):
            violations.extend(detail.get("violations", []))
    return body, violations


def _retry_delay_seconds(error):
    body, _ = _error_details(error)
    for detail in body.get("details", []):
        if (
            isinstance(detail, dict)
            and detail.get("@type", "").endswith("RetryInfo")
        ):
            retry_delay = detail.get("retryDelay", "")
            match = re.fullmatch(r"(\d+(?:\.\d+)?)s", retry_delay)
            if match:
                return float(match.group(1))

    match = re.search(
        r"retry in\s+(\d+(?:\.\d+)?)\s*(seconds?|secs?|s)\b",
        getattr(error, "message", ""),
        re.IGNORECASE,
    )
    if match:
        return float(match.group(1))
    return None


def _is_daily_quota(error, violations):
    message = getattr(error, "message", "").lower()
    if "per day" in message or "perday" in message:
        return True
    return any(
        "perday" in str(violation.get("quotaId", "")).lower()
        or "perday" in str(violation.get("quotaMetric", "")).lower()
        or "per day" in str(violation.get("description", "")).lower()
        for violation in violations
    )


def _is_short_rate_limit(error, violations):
    message = getattr(error, "message", "").lower()
    if "per minute" in message or "per-minute" in message:
        return True
    return any(
        "perminute" in str(violation.get("quotaId", "")).lower()
        or "per_minute" in str(violation.get("quotaMetric", "")).lower()
        for violation in violations
    )


def generate_content_with_retry(client, **request_args):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return client.models.generate_content(**request_args)
        except APIError as error:
            if error.code == 429:
                _, violations = _error_details(error)
                if _is_daily_quota(error, violations):
                    raise GeminiRequestError(
                        "Gemini's daily API quota is exhausted. No retries were "
                        "made. Wait until the quota resets, reduce the number of "
                        "feedback batches, or check the API project's quota."
                    ) from error
                if not _is_short_rate_limit(error, violations):
                    raise GeminiRequestError(
                        "Gemini's API quota or rate limit was reached. No retries "
                        "were made because this may be a daily quota limit. Check "
                        "the API project's current usage and quota."
                    ) from error
                retry_delay = _retry_delay_seconds(error)
                if retry_delay is None:
                    retry_delay = 2 ** attempt
                if retry_delay > MAX_RATE_LIMIT_WAIT_SECONDS:
                    raise GeminiRequestError(
                        "Gemini is rate limiting requests. Wait at least "
                        f"{math.ceil(retry_delay)} seconds before trying again.",
                        retryable=True,
                        retry_after_seconds=retry_delay,
                    ) from error
            elif error.code in {500, 502, 503, 504}:
                retry_delay = 2 ** attempt
            else:
                raise

            if attempt == MAX_ATTEMPTS:
                raise GeminiRequestError(
                    "Gemini is temporarily unavailable or rate limiting requests. "
                    "Please wait a few minutes before submitting again.",
                    retryable=True,
                ) from error

            delay = retry_delay + random.uniform(0, min(1, retry_delay * 0.2))
            logger.warning(
                "Gemini returned HTTP %s; retrying attempt %s/%s in %.1f seconds",
                error.code,
                attempt + 1,
                MAX_ATTEMPTS,
                delay,
            )
            time.sleep(delay)
