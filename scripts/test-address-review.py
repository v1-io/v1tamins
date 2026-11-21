#!/usr/bin/env python3
"""Offline tests for the bundled GitHub review ledger."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


HELPER = (
    Path(__file__).resolve().parents[1]
    / "plugins/v1tamins/skills/v1-address-review/scripts/fetch-review-ledger.py"
)
spec = importlib.util.spec_from_file_location("fetch_review_ledger", HELPER)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)

SHA = "a" * 40
REPO = "example/widgets"
URL = f"https://github.com/{REPO}"
LARGE_ID = 3_456_789_012


def metadata(url):
    return {
        "url": url, "number": int(url.split("/")[-1]), "title": "Refine widgets",
        "headRefOid": SHA, "headRefName": "refine-widgets", "baseRefName": "main",
    }


def connection(nodes, cursor=None):
    return {"nodes": nodes, "pageInfo": {"hasNextPage": cursor is not None, "endCursor": cursor}}


def thread(identifier, *ids, resolved=False, outdated=False, cursor=None):
    return {
        "id": identifier, "isResolved": resolved, "isOutdated": outdated,
        "comments": connection([{"databaseId": str(value)} for value in ids], cursor),
    }


def comment(identifier, body, **extra):
    return {
        "id": identifier, "html_url": f"{URL}/pull/1#comment-{identifier}",
        "body": body, "user": {"login": "reviewer"}, **extra,
    }


def check(identifier, **output):
    return {
        "id": identifier, "name": "Lint", "status": "completed", "conclusion": "success",
        "details_url": f"{URL}/runs/{identifier}",
        "output": {"title": None, "summary": None, "text": None, **output},
    }


def annotation(**extra):
    return {
        "path": "widget.py", "start_line": 2, "end_line": 4, "annotation_level": "warning",
        "title": None, "message": "Check this condition", "raw_details": "Repeated comparison",
        **extra,
    }


AGGREGATE = """### Code Review
`code-factory-rerun`

### P1 — Critical
#### Validate the widget
**`widget.py:42`**
Read the widget status.
~~~markdown
#### This is part of the example
~~~

### P2 — High
#### Bound the worker
The worker is unbounded.

### What looks good
#### Praise heading
Nice coverage.

### Previous Review Findings
| Finding | Status |
|---|---|
| Widget | Fixed |
"""


class FakeGH:
    """Return gh's slurped REST pages and GraphQL cursor pages."""

    def __init__(self):
        self.calls = []
        self.api = {
            "pulls?state=open&per_page=100": [[{"number": 1}], [{"number": 2}, {"number": 1}]],
            "pulls/1/comments?per_page=100": [
                [comment(LARGE_ID, "Review root", path="widget.py", line=8),
                 comment(20, "Already resolved", path="widget.py", line=9)],
                [comment(30, "Outdated", path="widget.py", original_line=10),
                 comment(40, "Both", path="widget.py", original_line=11),
                 comment(LARGE_ID + 1, "Reviewer follow-up", path="widget.py", line=8, in_reply_to_id=LARGE_ID)],
            ],
            "issues/1/comments?per_page=100": [
                [comment(51, "Ordinary discussion"), comment(52, AGGREGATE)],
                [comment(52, AGGREGATE), comment(53, AGGREGATE.replace("Fixed", "Open"))],
            ],
            "pulls/1/reviews?per_page=100": [
                [comment(61, "Top-level request", state="CHANGES_REQUESTED", commit_id=SHA)],
                [comment(62, "No changes requested", state="APPROVED", commit_id=SHA),
                 comment(63, "  ", state="APPROVED", commit_id=SHA),
                 comment(64, "Private draft", state="PENDING", commit_id=SHA)],
            ],
            f"commits/{SHA}/check-suites?per_page=1": {"total_count": 2, "check_suites": [{"id": 500}]},
            f"commits/{SHA}/check-runs?filter=all&per_page=100": [
                {"check_runs": [check(70, title="Warnings", summary="One warning", text="Use the API")]},
                {"check_runs": [check(71, title="Warnings", summary="One warning", text="Use the API")]},
            ],
            "check-runs/70/annotations?per_page=100": [[annotation()], [annotation(start_line=5, end_line=5)]],
            "check-runs/71/annotations?per_page=100": [[annotation()]],
        }
        self.thread_pages = {
            None: connection([thread("thread-open", LARGE_ID, cursor="reply-page"),
                              thread("thread-resolved", 20, resolved=True)], "threads-next"),
            "threads-next": connection([thread("thread-outdated", 30, outdated=True),
                                        thread("thread-both", 40, resolved=True, outdated=True)]),
        }
        self.reply_pages = {"reply-page": thread("thread-open", LARGE_ID + 1)}
        self.metadata_for = metadata
        self.error_endpoint = None

    def __call__(self, *args):
        self.calls.append(args)
        if args[:3] == ("repo", "view", "--json"):
            return {"nameWithOwner": REPO, "url": URL}
        if args[:2] == ("pr", "view"):
            return self.metadata_for(args[2])
        if args[:2] == ("api", "graphql"):
            return self.graphql(args)
        if args[0] != "api" or args[2:4] not in (("--hostname", "github.com"), ("--hostname", "github.example")):
            raise AssertionError(args)
        if args[4:6] != ("--method", "GET"):
            raise AssertionError("REST requests must explicitly use GET")
        _, _, repo, endpoint = args[1].split("/", 3)
        if endpoint == self.error_endpoint:
            raise ledger.LedgerError("gh api failed (HTTP 403)")
        if endpoint.endswith("per_page=1"):
            if args[6:]:
                raise AssertionError(args)
            if repo != "widgets":
                return {"total_count": 0, "check_suites": []}
        elif args[6:] != ("--paginate", "--slurp"):
            raise AssertionError(args)
        if repo != "widgets" and "/check-runs?" in endpoint:
            return [{"check_runs": []}]
        if repo != "widgets" or "/2/" in endpoint:
            return [[]]
        return self.api[endpoint]

    def graphql(self, args):
        variables = dict(field.split("=", 1) for field in args[5::2])
        query = variables["query"]
        if not query.lstrip().startswith("query(") or "databaseId: fullDatabaseId" not in query:
            raise AssertionError(query)
        cursor = variables.get("cursor")
        if "thread" in variables:
            if "after: $cursor" not in query:
                raise AssertionError(query)
            return {"data": {"node": self.reply_pages[cursor]}}
        if variables["number"] == "1" and variables["repo"] == "widgets":
            page = self.thread_pages[cursor]
        else:
            page = connection([])
        return {"data": {"repository": {"pullRequest": {"headRefOid": SHA, "reviewThreads": page}}}}


class FetchReviewLedgerTests(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGH()
        self.github = ledger.GitHub(self.gh)

    def invoke(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            result = ledger.main(args, self.github)
        return result, out.getvalue(), err.getvalue()

    def fetch(self, *args):
        result, out, err = self.invoke("--format", "json", *args)
        self.assertEqual((result, err), (0, ""))
        return json.loads(out)["pull_requests"]

    def test_paginates_every_feedback_surface_and_joins_replies_to_threads(self):
        [result] = self.fetch("1")
        self.assertEqual(result["pr"]["headRefOid"], SHA)
        self.assertEqual(result["filtered"], {"review_comments": 3, "resolved": 2, "outdated": 2, "threads": 3})
        comments = [item for item in result["items"] if item["kind"] == "review_comment"]
        self.assertEqual([item["id"] for item in comments], [LARGE_ID, LARGE_ID + 1])
        self.assertEqual(comments[0]["thread"], {"id": "thread-open", "isResolved": False, "isOutdated": False})
        self.assertEqual(comments[1]["thread"], comments[0]["thread"])
        self.assertEqual(comments[1]["reply_to"], LARGE_ID)
        self.assertTrue(any(f"commits/{SHA}/check-runs?filter=all&per_page=100" in call[1] for call in self.gh.calls))
        checks = [item for item in result["items"] if item["kind"] == "check_run"]
        self.assertEqual(len(checks), 1)
        [check_run] = checks
        self.assertEqual(check_run["conclusion"], "success")
        self.assertIn("Use the API", check_run["body"])
        self.assertEqual(check_run["also_seen_in"], [{"id": 71, "url": f"{URL}/runs/71"}])
        annotations = [item for item in result["items"] if item["kind"] == "annotation"]
        self.assertEqual([(item["line"], item["end_line"]) for item in annotations], [(2, 4), (5, 5)])
        self.assertIn("Repeated comparison", annotations[0]["body"])
        self.assertEqual(annotations[0]["also_seen_in"], check_run["also_seen_in"])
        reviews = [item for item in result["items"] if item["kind"] == "review_body"]
        self.assertEqual([(item["id"], item["state"], item["commit_id"]) for item in reviews],
                         [(61, "CHANGES_REQUESTED", SHA), (62, "APPROVED", SHA)])

    def test_include_resolved_keeps_thread_flags_and_original_line(self):
        [result] = self.fetch("--include-resolved", "1")
        self.assertEqual(result["filtered"], dict(review_comments=0, resolved=0, outdated=0, threads=0))
        comments = {item["id"]: item for item in result["items"] if item["kind"] == "review_comment"}
        self.assertTrue(comments[20]["thread"]["isResolved"])
        self.assertTrue(comments[30]["thread"]["isOutdated"])
        self.assertEqual(comments[30]["line"], 10)
        self.assertTrue(comments[40]["thread"]["isResolved"] and comments[40]["thread"]["isOutdated"])

    def test_aggregate_findings_keep_round_links_and_summary(self):
        [result] = self.fetch("1")
        items = result["items"]
        findings = [item for item in items if item["kind"] == "aggregate_finding"]
        self.assertEqual([(item["severity"], item["title"]) for item in findings],
                         [("P1", "Validate the widget"), ("P2", "Bound the worker")])
        self.assertEqual((findings[0]["path"], findings[0]["line"]), ("widget.py", 42))
        self.assertIn("#### This is part of the example", findings[0]["body"])
        self.assertNotIn("Praise heading", json.dumps(items))
        self.assertEqual(findings[0]["also_seen_in"], [{"id": 53, "url": f"{URL}/pull/1#comment-53"}])
        context = [item for item in items if item.get("aggregate")]
        self.assertEqual([item["id"] for item in context], [52, 53])
        self.assertIn("| Widget | Fixed |", context[0]["body"])
        self.assertIn("| Widget | Open |", context[1]["body"])
        [ordinary] = [item for item in items if item["kind"] == "issue_comment" and not item["aggregate"]]
        self.assertEqual(ordinary["body"], "Ordinary discussion")

    def test_summary_and_unmarked_comment_are_preserved(self):
        summary = "## Code Factory\n\n### Previous Review Findings\n| Widget | Fixed |"
        self.assertEqual(ledger.parse_aggregate(summary), ([], summary))
        ordinary = "### P1\n#### A concern\nNo known marker"
        self.assertEqual(ledger.parse_aggregate(ordinary), ([], ordinary))

    def test_distinct_aggregate_body_with_same_title_is_preserved(self):
        self.gh.api["issues/1/comments?per_page=100"][1][1]["body"] = AGGREGATE.replace(
            "Read the widget status.", "Inspect the widget timeout."
        )
        [result] = self.fetch("1")
        self.assertEqual(len([item for item in result["items"] if item["kind"] == "aggregate_finding"]), 3)

    def test_unicode_truncation_has_source_and_is_compact(self):
        body = "🧪" * 60_000
        records = [comment(99, body)]
        self.gh.api["issues/1/comments?per_page=100"] = [records]
        [result] = self.fetch("1")
        [item] = [item for item in result["items"] if item["kind"] == "issue_comment"]
        self.assertEqual(item["url"], f"{URL}/pull/1#comment-99")
        self.assertTrue(item["body"].endswith(ledger.TRUNCATED))
        self.assertTrue(item["body"].startswith("🧪" * 100))
        self.assertLessEqual(len(item["body"]), ledger.BODY_LIMIT)
        projected_size = len(json.dumps(result, ensure_ascii=False).encode())
        raw_size = len(json.dumps(records, ensure_ascii=False).encode())
        self.assertLess(projected_size / raw_size, 0.05)

    def test_long_check_keeps_excerpts_from_both_fields(self):
        self.gh.api[f"commits/{SHA}/check-runs?filter=all&per_page=100"] = [
            {"check_runs": [check(70, summary="summary " * 1500, text="check details " * 1000)]},
        ]
        [result] = self.fetch("1")
        [item] = [item for item in result["items"] if item["kind"] == "check_run"]
        self.assertIn("summary summary", item["body"])
        self.assertIn("check details check details", item["body"])
        self.assertEqual(item["body"].count(ledger.TRUNCATED), 2)
        self.assertLessEqual(len(item["body"]), ledger.BODY_LIMIT)

    def test_markdown_contains_ids_links_states_and_page_counts(self):
        status, text, error = self.invoke("--include-resolved", "1")
        self.assertEqual((status, error), (0, ""))
        for value in (SHA, f"[{REPO}#1]({URL}/pull/1)", f"reply to {LARGE_ID}", "thread thread-outdated (outdated)",
                      f"[71]({URL}/runs/71)", "Filtered 0 review comments"):
            self.assertIn(value, text)

    def test_explicit_batch_deduplicates_numeric_and_url_and_scopes_repo(self):
        results = self.fetch("2", f"{URL}/pull/1/files#diff-1", f"https://GITHUB.COM/{REPO.upper()}/pull/1",
                             "1", "https://github.example/example/gadgets/pull/3")
        self.assertEqual([(item["pr"]["repo"], item["pr"]["number"]) for item in results],
                         [(REPO, 2), (REPO, 1), ("example/gadgets", 3)])
        self.assertTrue(any(call[:4] == ("api", "repos/example/gadgets/pulls/3/comments?per_page=100",
                                        "--hostname", "github.example") for call in self.gh.calls))

    def test_url_only_does_not_use_current_repository(self):
        self.fetch(f"{URL}/pull/1")
        self.assertFalse(any(call[0] == "repo" for call in self.gh.calls))

    def test_all_open_reads_each_page_and_handles_empty_repo(self):
        results = self.fetch("--all-open")
        self.assertEqual([item["pr"]["number"] for item in results], [1, 2])
        self.gh.api["pulls?state=open&per_page=100"] = [[]]
        self.assertEqual(self.fetch("--all-open"), [])
        self.assertEqual(self.invoke("--all-open"), (0, "No open pull requests.\n", ""))

    def test_check_suite_cap_uses_per_suite_check_pagination(self):
        self.gh.api[f"commits/{SHA}/check-suites?per_page=1"]["total_count"] = 1001
        self.gh.api[f"commits/{SHA}/check-suites?per_page=100"] = [
            {"check_suites": [{"id": 500}]}, {"check_suites": [{"id": 501}]},
        ]
        self.gh.api["check-suites/500/check-runs?filter=all&per_page=100"] = [
            {"check_runs": []}, {"check_runs": [check(70)]},
        ]
        self.gh.api["check-suites/501/check-runs?filter=all&per_page=100"] = [{"check_runs": [check(71)]}]
        [result] = self.fetch("1")
        [item] = [item for item in result["items"] if item["kind"] == "check_run"]
        self.assertEqual(item["also_seen_in"][0]["id"], 71)
        self.assertNotIn(f"repos/{REPO}/commits/{SHA}/check-runs?filter=all&per_page=100",
                         [call[1] for call in self.gh.calls])

    def test_batch_isnt_printed_if_later_pr_errors(self):
        self.gh.error_endpoint = "issues/2/comments?per_page=100"
        status, out, error = self.invoke("--format", "json", "1", "2")
        self.assertEqual((status, out), (1, ""))
        self.assertIn(f"{URL}/pull/2", error)
        self.assertIn("HTTP 403", error)

    def test_malformed_page_is_an_error_not_zero_findings(self):
        self.gh.api["check-runs/71/annotations?per_page=100"] = [{"message": "unexpected object"}]
        status, out, error = self.invoke("1")
        self.assertEqual((status, out), (1, ""))
        self.assertIn("incomplete feedback", error)

    def test_unmatched_review_comment_fails_closed(self):
        self.gh.reply_pages["reply-page"] = thread("thread-open")
        status, out, error = self.invoke("1")
        self.assertEqual((status, out), (1, ""))
        self.assertIn(f"No GraphQL thread matched review comment {LARGE_ID + 1}", error)

    def test_graphql_partial_error_does_not_look_like_empty_page(self):
        with patch.object(self.gh, "graphql", return_value={"data": {}, "errors": [{"message": "denied"}]}):
            status, out, error = self.invoke("1")
        self.assertEqual((status, out), (1, ""))
        self.assertIn("GraphQL returned errors", error)

    def test_graphql_repeated_or_missing_cursor_is_rejected(self):
        for cursor in ("threads-next", ""):
            with self.subTest(cursor=cursor):
                self.gh.thread_pages["threads-next"] = connection([], cursor)
                status, out, error = self.invoke("1")
                self.assertEqual((status, out), (1, ""))
                self.assertIn("GraphQL pagination did not advance", error)

    def test_missing_metadata_and_bad_head_fail_before_api_calls(self):
        for bad in ({}, None, {**metadata(f"{URL}/pull/1"), "headRefOid": ""}):
            with self.subTest(bad=bad):
                self.gh.metadata_for = lambda url: bad
                self.gh.calls.clear()
                status, out, error = self.invoke(f"{URL}/pull/1")
                self.assertEqual((status, out), (1, ""))
                self.assertIn("PR metadata unavailable", error)
                self.assertEqual([call[0] for call in self.gh.calls], ["pr"])

    def test_head_change_at_end_discards_ledger(self):
        responses = iter([metadata(f"{URL}/pull/1"), {**metadata(f"{URL}/pull/1"), "headRefOid": "b" * 40}])
        self.gh.metadata_for = lambda url: next(responses)
        status, out, error = self.invoke("1")
        self.assertEqual((status, out), (1, ""))
        self.assertIn("PR head changed during collection", error)

    def test_rejects_bad_cli_arguments(self):
        for args in ((), ("--all-open", "1"), ("--format", "yaml", "1")):
            with self.subTest(args=args), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                ledger.main(args, self.github)
            self.assertEqual(error.exception.code, 2)
        for arg in ("0", "--not-an-input", "http://github.com/example/widgets/pull/1",
                    "https://user@github.com/example/widgets/pull/1", "https://github.com/../widgets/pull/1"):
            with self.subTest(arg=arg):
                status, out, error = self.invoke("--", arg)
                self.assertEqual((status, out), (1, ""))
                self.assertIn("Expected a positive PR number", error)
        self.assertEqual(self.gh.calls, [])

    def test_gh_process_errors_are_explicit_and_discard_partial_stdout(self):
        for outcome, message in (
            (FileNotFoundError(), "GitHub CLI (gh) is required"),
            (subprocess.TimeoutExpired(["gh", "api"], 60), "TimeoutExpired"),
            (subprocess.CompletedProcess(["gh"], 1, '{"partial": true}', "gh: access denied"), "access denied"),
            (subprocess.CompletedProcess(["gh"], 0, "unexpected output", ""), "invalid JSON"),
        ):
            with self.subTest(message=message), patch.object(ledger.subprocess, "run") as run:
                if isinstance(outcome, Exception):
                    run.side_effect = outcome
                else:
                    run.return_value = outcome
                with self.assertRaisesRegex(ledger.LedgerError, message.replace("(gh)", r"\(gh\)")):
                    ledger.gh_json("api", "graphql")


if __name__ == "__main__":
    unittest.main()
