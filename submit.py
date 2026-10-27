"""Submit this project to an evaluation server, if your event provides one.

    uv run submit.py              # practice evaluation: wait for the result, show it
    uv run submit.py --final      # final submission: show the receipt
    uv run submit.py --status ID  # show a submission, waiting for its result

The archive is `submission.zip` as `spacecraft-ops-challenge pack` builds it: the
`submission/` directory and `pyproject.toml`. The server address and token come from
`--server` and `--token`, or from the environment variables `EVALUATION_SERVER_URL`
and `EVALUATION_SERVER_TOKEN`. You are identified by `git config user.email` and
`git config user.name` unless `--participant-id` and `--participant-name` say
otherwise.

The server speaks a small HTTP protocol, relative to its base URL:

    POST submissions?kind=practice|final&participant_id=...&participant_name=...
        body: submission.zip; answers with a receipt: id, status, sha256, ...
    GET  submissions/{id}
        the receipt with its current status; a completed practice submission also
        carries the result document of `spacecraft-ops-challenge check --json`
        under "result"

Errors are JSON objects with a "detail" message.
"""

import argparse
import http.client
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
URL_VARIABLE = "EVALUATION_SERVER_URL"
TOKEN_VARIABLE = "EVALUATION_SERVER_TOKEN"
PENDING_STATUSES = frozenset({"queued", "running"})
UPLOAD_BYTES_PER_S = 100_000
"""Slowest upload rate to allow for, which extends the timeout of large submissions."""


class ServerError(Exception):
    """Raised when the evaluation server cannot be reached or rejects a request."""


def git_config(key: str, directory: Path = PROJECT_DIR) -> str | None:
    """The value of `git config <key>` in `directory`, or `None` if it is not set."""
    try:
        completed = subprocess.run(
            ["git", "config", key],
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:  # Git is not installed
        return None
    return completed.stdout.strip() or None


class EvaluationServer:
    """Client of the evaluation server at the base URL `url`."""

    def __init__(self, url: str, token: str | None = None, timeout_s: float = 60.0):
        url = url.strip()
        if not url:
            raise ServerError("no evaluation server address is set")
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            raise ServerError(
                f"the server address {url!r} must start with http:// or https://"
            )
        self.url = url.rstrip("/") + "/"
        self.token = (token or "").strip() or None
        self.timeout_s = timeout_s

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        data: bytes | None = None,
    ) -> dict[str, Any]:
        url = urllib.parse.urljoin(self.url, path)
        if params:
            url += "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/zip")
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        # A socket timeout bounds the whole upload, so it grows with the archive.
        timeout_s = self.timeout_s + len(data or b"") / UPLOAD_BYTES_PER_S
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                answer = json.load(response)
        except urllib.error.HTTPError as error:
            try:
                detail = json.load(error).get("detail")
            except (ValueError, AttributeError):
                detail = None
            raise ServerError(
                f"the server answered {error.code}: {detail or error.reason}"
            ) from None
        except (urllib.error.URLError, OSError) as error:
            reason = getattr(error, "reason", error)
            raise ServerError(f"cannot reach {self.url}: {reason}") from None
        except (http.client.HTTPException, ValueError) as error:
            raise ServerError(f"the server sent an invalid answer: {error!r}") from None
        if not isinstance(answer, dict):
            raise ServerError("the server sent an invalid answer: not a JSON object")
        return answer

    def submit(
        self,
        archive: bytes,
        participant_id: str,
        participant_name: str,
        *,
        final: bool = False,
    ) -> dict[str, Any]:
        """Send `archive` as a practice or final submission and return the receipt."""
        params = {
            "kind": "final" if final else "practice",
            "participant_id": participant_id,
            "participant_name": participant_name,
        }
        return self._request("POST", "submissions", params, archive)

    def submission(self, submission_id: str) -> dict[str, Any]:
        """The receipt of the submission `submission_id` with its current status."""
        quoted = urllib.parse.quote(submission_id, safe="")
        return self._request("GET", f"submissions/{quoted}")

    def wait(
        self,
        submission_id: str,
        *,
        poll_s: float = 2.0,
        on_status: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Poll the submission until its evaluation has ended, and return it."""
        status = None
        while True:
            document = self.submission(submission_id)
            if document.get("status") != status:
                status = document.get("status")
                if on_status is not None:
                    on_status(str(status))
            if status not in PENDING_STATUSES:
                return document
            time.sleep(poll_s)


def receipt_lines(receipt: dict[str, Any]) -> list[str]:
    """The receipt as `label: value` lines."""
    participant = receipt.get("participant") or {}
    return [
        f"Submission: {receipt.get('id')}",
        f"Kind:       {receipt.get('kind')}",
        f"Status:     {receipt.get('status')}",
        f"Received:   {receipt.get('received_at')}",
        f"SHA-256:    {receipt.get('sha256')}",
        f"Submitter:  {participant.get('name')} <{participant.get('id')}>",
    ]


def main(argv: Sequence[str] | None = None) -> int:
    """Pack the project, submit it, and show the receipt or the practice result."""
    parser = argparse.ArgumentParser(
        prog="uv run submit.py", description=__doc__.split("\n\n")[0]
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--final", action="store_true", help="submit as your final submission"
    )
    action.add_argument(
        "--status", metavar="ID", help="show the submission ID instead of submitting"
    )
    parser.add_argument("--server", help=f"base URL (default: ${URL_VARIABLE})")
    parser.add_argument("--token", help=f"server token (default: ${TOKEN_VARIABLE})")
    parser.add_argument("--participant-id", help="default: git config user.email")
    parser.add_argument("--participant-name", help="default: git config user.name")
    args = parser.parse_args(argv)

    from spacecraft_ops_challenge.cli import format_check_report
    from spacecraft_ops_challenge.judge.reporting import (
        EvaluationResult,
        ResultFormatError,
        problem_outcomes,
    )
    from spacecraft_ops_challenge.judge.submission import (
        SubmissionError,
        build_submission,
    )

    participant_id = args.participant_id or git_config("user.email")
    participant_name = args.participant_name or git_config("user.name")
    if args.status is None and not (participant_id and participant_name):
        parser.error(
            "set git config user.email and user.name, "
            "or pass --participant-id and --participant-name"
        )
    receipt = None
    try:
        server = EvaluationServer(
            args.server or os.environ.get(URL_VARIABLE, ""),
            args.token or os.environ.get(TOKEN_VARIABLE),
        )
        if args.status is not None:
            receipt = server.submission(args.status)
        else:
            archive = build_submission(PROJECT_DIR)
            kind = "final" if args.final else "practice"
            print(f"Submitting as {participant_name} <{participant_id}> ({kind})")
            receipt = server.submit(
                archive, participant_id, participant_name, final=args.final
            )
        print("\n".join(receipt_lines(receipt)))
        if receipt.get("kind") == "final":
            return 0
        document = server.wait(
            str(receipt.get("id")),
            on_status=lambda status: print(f"Status: {status}"),
        )
    except (ServerError, SubmissionError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        later = (
            ""
            if receipt is None
            else "; the server keeps the submission, see it later with "
            f"`uv run submit.py --status {receipt.get('id')}`"
        )
        print(f"interrupted{later}", file=sys.stderr)
        return 130
    if document.get("status") != "completed":
        print(f"The evaluation {document.get('status')}: {document.get('error')}")
        return 1
    try:
        result = EvaluationResult.from_dict(document["result"])
    except (KeyError, TypeError, ResultFormatError) as error:
        print(f"error: the server sent an invalid result: {error}", file=sys.stderr)
        return 2
    print()
    print(format_check_report(str(receipt.get("id")), result))
    return 1 if problem_outcomes(result.outcomes) else 0


if __name__ == "__main__":
    sys.exit(main())
