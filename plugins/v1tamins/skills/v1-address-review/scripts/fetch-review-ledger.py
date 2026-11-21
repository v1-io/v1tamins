#!/usr/bin/env python3
"""Read GitHub PR feedback through gh and emit a compact, head-pinned ledger."""

import argparse
import html
import json
import os
import re
import subprocess
import sys
from typing import NamedTuple
from urllib.parse import urlsplit

BODY_LIMIT = 1200
TRUNCATED = "[… truncated, see source]"
PR_PATH = re.compile(r"/([\w.-]+)/([\w.-]+)/pull/([1-9][0-9]*)(?:/.*)?", re.ASCII)
REPO_NAME = re.compile(r"[\w.-]+/[\w.-]+", re.ASCII)
SHA = re.compile(r"[a-f0-9]{40}", re.ASCII)
AGGREGATE_MARKER = re.compile(
    r"^[ \t]*(?:#{2,3}[ \t]+(?:Code Review|Code Factory)\b|\*\*Claude finished\b)"
    r"|code-factory-rerun",
    re.IGNORECASE | re.MULTILINE,
)
HEADING = re.compile(r"^[ ]{0,3}(#{1,6})[ \t]+(.+?)\s*$")
FENCE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})(.*)$")
LOCATION = re.compile(r"\*\*`([^`\n]+):(\d+)`\*\*")
SEVERITY = re.compile(r"^(P[123])\b", re.IGNORECASE)

# Alias the 64-bit ID to the REST join key. GraphQL's legacy databaseId is 32-bit.
THREAD_FIELDS = """
    id isResolved isOutdated
    comments(first: 50%s) {
        nodes { databaseId: fullDatabaseId }
        pageInfo { hasNextPage endCursor }
    }
"""
THREADS_QUERY = """
query($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
    repository(owner: $owner, name: $repo) {
        pullRequest(number: $number) {
            headRefOid
            reviewThreads(first: 50, after: $cursor) {
                nodes { %s }
                pageInfo { hasNextPage endCursor }
            }
        }
    }
}
""" % (THREAD_FIELDS % "")
THREAD_COMMENTS_QUERY = """
query($thread: ID!, $cursor: String!) {
    node(id: $thread) {
        ... on PullRequestReviewThread { %s }
    }
}
""" % (THREAD_FIELDS % ", after: $cursor")


class LedgerError(Exception):
    """Feedback collection failed and no complete ledger is available."""


class Repository(NamedTuple):
    host: str
    name: str

    @property
    def url(self):
        return f"https://{self.host}/{self.name}"


class Target(NamedTuple):
    repo: Repository
    number: int

    @property
    def url(self):
        return f"{self.repo.url}/pull/{self.number}"

    @property
    def key(self):
        return self.repo.host, self.repo.name.lower(), self.number


def parse_target(value):
    """Return a PR number or a URL scoped to its own repository."""
    if re.fullmatch(r"[1-9][0-9]*", value):
        return int(value)
    try:
        url = urlsplit(value)
    except ValueError:
        url = None
    if url and url.scheme == "https" and re.fullmatch(r"[a-z0-9.-]+", url.netloc, re.I):
        match = PR_PATH.fullmatch(url.path)
        if match:
            owner, repo, number = match.groups()
            if owner not in {".", ".."} and repo not in {".", ".."}:
                return Target(Repository(url.netloc.lower(), f"{owner}/{repo}"), int(number))
    raise LedgerError(f"Expected a positive PR number or an HTTPS GitHub PR URL: {value!r}")


def gh_json(*args):
    env = {**os.environ, "GH_PROMPT_DISABLED": "1", "GH_DEBUG": ""}
    try:
        result = subprocess.run(
            ["gh", *args], capture_output=True, text=True, encoding="utf-8",
            stdin=subprocess.DEVNULL, env=env, timeout=60,
        )
    except FileNotFoundError as error:
        raise LedgerError("GitHub CLI (gh) is required. Install it and authenticate to GitHub.") from error
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as error:
        raise LedgerError(f"gh {args[0]} could not complete: {error.__class__.__name__}") from error
    if result.returncode:
        # For GraphQL failures gh may put the error on stdout; it can also include
        # partial data there. Only report stderr and never accept partial output.
        detail = result.stderr.strip()[:500] or f"exit {result.returncode}"
        raise LedgerError(f"gh {args[0]} failed ({detail})")
    try:
        return json.loads(result.stdout)
    except (ValueError, RecursionError) as error:
        raise LedgerError(f"gh {args[0]} returned invalid JSON") from error


def array(value):
    if not isinstance(value, list):
        raise ValueError("expected an array")
    return value


def field(record, key, kind):
    value = record[key]
    if type(value) is not kind:
        raise ValueError(f"invalid {key} field")
    return value


def text_field(record, key):
    value = record[key]
    if value is None:
        return ""
    return field(record, key, str)


class GitHub:
    def __init__(self, run=gh_json):
        self.run = run

    def current_repo(self):
        try:
            repo = self.run("repo", "view", "--json", "nameWithOwner,url")
            name = field(repo, "nameWithOwner", str)
            url = field(repo, "url", str)
            if not REPO_NAME.fullmatch(name) or not url.lower().endswith(f"/{name.lower()}"):
                raise ValueError("invalid repository identity")
            return parse_target(f"{url}/pull/1").repo
        except (KeyError, ValueError, TypeError, LedgerError) as error:
            raise LedgerError(f"Could not identify the current GitHub repository: {error}") from error

    def rest(self, repo, route, query="per_page=100", *, paginate=True):
        endpoint = f"repos/{repo.name}/{route}?{query}"
        args = ["api", endpoint, "--hostname", repo.host, "--method", "GET"]
        if paginate:
            args.extend(("--paginate", "--slurp"))
        try:
            return self.run(*args)
        except LedgerError as error:
            raise LedgerError(f"{repo.name}/{route}: {error}") from error

    def rest_items(self, repo, route, query="per_page=100", *, key=None):
        pages = array(self.rest(repo, route, query))
        if not pages:
            raise LedgerError(f"{route}: gh returned no response pages")
        return [item for page in pages for item in array(page[key] if key else page)]

    def metadata(self, target):
        try:
            meta = self.run(
                "pr", "view", target.url, "--json",
                "number,title,url,headRefOid,headRefName,baseRefName",
            )
            actual = parse_target(field(meta, "url", str))
            sha = field(meta, "headRefOid", str)
            if actual.key != target.key or field(meta, "number", int) != target.number:
                raise ValueError("PR identity differs from the requested target")
            if not SHA.fullmatch(sha):
                raise ValueError("headRefOid is missing or invalid")
            for key in ("title", "headRefName", "baseRefName"):
                field(meta, key, str)
            return {"repo": target.repo.name, **meta}
        except (KeyError, ValueError, TypeError, AttributeError, LedgerError) as error:
            raise LedgerError(f"{target.url}: PR metadata unavailable ({error})") from error

    def graphql(self, host, query, *, number=None, **variables):
        args = ["api", "graphql", "--hostname", host, "-f", f"query={query}"]
        if number is not None:
            args.extend(("-F", f"number={number}"))
        for name, value in variables.items():
            if value is not None:
                args.extend(("-f", f"{name}={value}"))
        data = self.run(*args)
        if not isinstance(data, dict) or data.get("errors") or not isinstance(data.get("data"), dict):
            raise LedgerError("GraphQL returned errors or no data for review threads")
        return data["data"]

    def threads(self, target, sha):
        owner, name = target.repo.name.split("/")

        def thread_page(cursor):
            data = self.graphql(
                target.repo.host, THREADS_QUERY, number=target.number,
                owner=owner, repo=name, cursor=cursor,
            )
            pr = data["repository"]["pullRequest"]
            if pr["headRefOid"] != sha:
                raise LedgerError("PR head changed during collection. Fetch the ledger again.")
            return pr["reviewThreads"]

        def comment_page(thread, cursor):
            data = self.graphql(target.repo.host, THREAD_COMMENTS_QUERY, thread=thread["id"], cursor=cursor)
            node = data["node"]
            if thread_state(node) != thread_state(thread):
                raise LedgerError("Review thread changed during collection. Fetch the ledger again.")
            return node["comments"]

        threads = []
        for thread in connection_nodes(thread_page):
            comments = connection_nodes(lambda cursor: comment_page(thread, cursor), thread["comments"])
            threads.append((thread_state(thread), list(comments)))
        return threads

    def checks(self, repo, sha):
        # GitHub caps the commit endpoint at 1000 suites, regardless of pagination.
        suites = f"commits/{sha}/check-suites"
        count = field(self.rest(repo, suites, "per_page=1", paginate=False), "total_count", int)
        query = "filter=all&per_page=100"
        if count <= 1000:
            return self.rest_items(repo, f"commits/{sha}/check-runs", query, key="check_runs")
        runs = []
        for suite in unique_records(self.rest_items(repo, suites, key="check_suites")):
            runs.extend(self.rest_items(repo, f"check-suites/{suite['id']}/check-runs", query, key="check_runs"))
        return runs

    def collect(self, target, include_resolved):
        try:
            meta = self.metadata(target)
            sha = meta["headRefOid"]
            repo = target.repo
            number = target.number
            threads = self.threads(target, sha)
            line_comments = self.rest_items(repo, f"pulls/{number}/comments")
            issue_comments = self.rest_items(repo, f"issues/{number}/comments")
            reviews = self.rest_items(repo, f"pulls/{number}/reviews")
            checks = [
                (run, self.rest_items(repo, f"check-runs/{run['id']}/annotations"))
                for run in unique_records(self.checks(repo, sha))
            ]
            if self.metadata(target)["headRefOid"] != sha:
                raise LedgerError("PR head changed during collection. Fetch the ledger again.")
            return build_ledger(meta, threads, line_comments, issue_comments, reviews, checks, include_resolved)
        except (KeyError, ValueError, TypeError, LedgerError) as error:
            if str(error).startswith(f"{target.url}:"):
                raise
            raise LedgerError(f"{target.url}: incomplete feedback ({error})") from error


def connection_nodes(fetch_page, first=None):
    """Yield GraphQL nodes, requiring a fresh cursor for each additional page."""
    page = fetch_page(None) if first is None else first
    seen = set()
    while True:
        yield from array(page["nodes"])
        info = page["pageInfo"]
        if not field(info, "hasNextPage", bool):
            return
        cursor = field(info, "endCursor", str)
        if not cursor or cursor in seen:
            raise LedgerError("GraphQL pagination did not advance")
        seen.add(cursor)
        page = fetch_page(cursor)


def thread_state(thread):
    return {key: field(thread, key, kind) for key, kind in (
        ("id", str), ("isResolved", bool), ("isOutdated", bool),
    )}


def index_threads(threads):
    by_comment = {}
    for state, comments in threads:
        for comment in comments:
            comment_id = int(comment["databaseId"])
            if by_comment.setdefault(comment_id, state) != state:
                raise LedgerError(f"Conflicting review threads for comment {comment_id}")
    return by_comment


def unique_records(records):
    seen = set()
    for record in records:
        identifier = field(record, "id", int)
        if identifier not in seen:
            yield record
            seen.add(identifier)


def excerpt(body, limit=BODY_LIMIT):
    body = body.strip()
    if len(body) <= limit:
        return body
    return f"{body[:limit - len(TRUNCATED) - 1].rstrip()}\n{TRUNCATED}"


def check_body(*parts):
    sections = tuple(dict.fromkeys(part.strip() for part in parts if part.strip()))
    if len("\n\n".join(sections)) <= BODY_LIMIT:
        return "\n\n".join(sections), sections
    limit = (BODY_LIMIT - 2 * (len(sections) - 1)) // len(sections)
    return "\n\n".join(excerpt(part, limit) for part in sections), sections


def heading_sections(body):
    """Group text under real Markdown headings, keeping fenced examples intact."""
    fence = None
    start, depth, title = 0, 0, ""
    offset = 0
    for line in body.splitlines(keepends=True):
        boundary = FENCE.match(line)
        if fence:
            if boundary and boundary[1].startswith(fence) and not boundary[2].strip():
                fence = None
        elif boundary:
            fence = boundary[1]
        else:
            heading = HEADING.match(line)
            if heading:
                yield depth, title, body[start:offset]
                start, depth, title = offset, len(heading[1]), heading[2]
        offset += len(line)
    yield depth, title, body[start:]


def parse_aggregate(body):
    """Split a marked aggregate into findings and remaining status context."""
    if not AGGREGATE_MARKER.search(body):
        return [], body
    findings, context = [], []
    severity = None
    praise_depth = None
    finding = None
    for depth, title, section in heading_sections(body):
        if praise_depth is not None and depth > praise_depth:
            continue
        praise_depth = None
        if finding and depth <= finding["depth"]:
            finding = None
        if severity and depth <= severity[0]:
            severity = None
        if title.strip(" #").casefold().startswith("what looks good"):
            praise_depth = depth
            continue
        priority = SEVERITY.match(title)
        if priority and depth == 3:
            severity = (depth, priority[1].upper())
        elif severity and depth == severity[0] + 1:
            finding = {"severity": severity[1], "title": title, "depth": depth, "body": ""}
            findings.append(finding)
            section = section.partition("\n")[2]
        if finding:
            finding["body"] += section
        elif not (priority and depth == 3 and not section.partition("\n")[2].strip()):
            context.append(section)
    for finding in findings:
        del finding["depth"]
        location = LOCATION.search(finding["body"])
        if location:
            finding.update(path=location[1], line=int(location[2]))
    return findings, "".join(context)


def comment_item(kind, record):
    user = record.get("user")
    return {
        "kind": kind, "id": record["id"], "url": field(record, "html_url", str),
        "author": user["login"] if user else "[deleted]",
    }


def check_items(meta, checks):
    for run, annotations in checks:
        run_id = run["id"]
        url = run.get("details_url") or run.get("html_url") or f"{meta['url']}/checks"
        name = field(run, "name", str)
        output = run["output"]
        status = field(run, "status", str)
        conclusion = text_field(run, "conclusion")
        title = text_field(output, "title")
        body, sections = check_body(text_field(output, "summary"), text_field(output, "text"))
        item = {
            "kind": "check_run", "id": run_id, "url": url, "name": name,
            "status": status, "conclusion": conclusion, "title": title, "body": body,
        }
        yield item, (name, status, conclusion, title, sections)
        for annotation in annotations:
            path = field(annotation, "path", str)
            line = field(annotation, "start_line", int)
            end_line = field(annotation, "end_line", int)
            title = text_field(annotation, "title")
            level = field(annotation, "annotation_level", str)
            message = field(annotation, "message", str)
            details = text_field(annotation, "raw_details")
            body, sections = check_body(message, details)
            item = {
                "kind": "annotation", "id": run_id, "url": url, "name": name,
                "level": level, "path": path, "line": line, "end_line": end_line,
                "title": title, "body": body,
            }
            yield item, (name, level, path, line, end_line, annotation.get("start_column"),
                         annotation.get("end_column"), title, sections)


def add_distinct(items, seen, item, fingerprint):
    """Merge exact aggregate/check repeats while retaining every source."""
    key = (item["kind"], fingerprint)
    if key in seen:
        prior = seen[key]
        source = {"id": item["id"], "url": item["url"]}
        if (source["id"], source["url"]) != (prior["id"], prior["url"]):
            sources = prior.setdefault("also_seen_in", [])
            if source not in sources:
                sources.append(source)
        return
    seen[key] = item
    items.append(item)


def build_ledger(meta, threads, line_comments, issue_comments, reviews, checks, include_resolved=False):
    """Project API records without making semantic or mutation decisions."""
    items, seen = [], {}
    filtered = dict(review_comments=0, resolved=0, outdated=0, threads=0)
    filtered_threads = set()
    by_comment = index_threads(threads)
    for record in unique_records(line_comments):
        thread = by_comment.get(record["id"])
        if thread is None:
            raise LedgerError(f"No GraphQL thread matched review comment {record['id']}")
        if not include_resolved and (thread["isResolved"] or thread["isOutdated"]):
            filtered["review_comments"] += 1
            filtered["resolved"] += thread["isResolved"]
            filtered["outdated"] += thread["isOutdated"]
            filtered_threads.add(thread["id"])
            continue
        item = comment_item("review_comment", record)
        item.update(thread=thread, path=record["path"], line=record.get("line") or record.get("original_line"),
                    reply_to=record.get("in_reply_to_id"), body=text_field(record, "body"))
        items.append(item)
    filtered["threads"] = len(filtered_threads)

    for record in unique_records(issue_comments):
        item = comment_item("issue_comment", record)
        findings, context = parse_aggregate(text_field(record, "body"))
        if context.strip() or not findings:
            items.append({**item, "body": context, "aggregate": bool(findings or AGGREGATE_MARKER.search(context))})
        for finding in findings:
            key = (item["author"], finding["severity"], finding.get("path"), finding.get("line"),
                   finding["title"], finding["body"].strip())
            add_distinct(items, seen, {**item, **finding, "kind": "aggregate_finding"}, key)
    for record in unique_records(reviews):
        body = text_field(record, "body")
        state = field(record, "state", str)
        if body.strip() and state != "PENDING":
            item = comment_item("review_body", record)
            items.append({**item, "state": state, "commit_id": record["commit_id"], "body": body})
    for item, fingerprint in check_items(meta, checks):
        add_distinct(items, seen, item, fingerprint)
    for item in items:
        item["body"] = excerpt(item["body"])
        if "title" in item:
            item["title"] = excerpt(item["title"])
    return {"pr": meta, "filtered": filtered, "items": items}


def collect_batch(github, inputs, all_open, include_resolved):
    targets = [parse_target(value) for value in inputs]
    if all_open or any(isinstance(target, int) for target in targets):
        repo = github.current_repo()
        if all_open:
            targets = [field(record, "number", int) for record in
                       github.rest_items(repo, "pulls", "state=open&per_page=100")]
        targets = [Target(repo, target) if isinstance(target, int) else target for target in targets]
    by_key = {}
    for target in targets:
        if target.key not in by_key:
            by_key[target.key] = github.collect(target, include_resolved)
    return {"pull_requests": list(by_key.values())}


def render_markdown(batch):
    lines = []
    for ledger in batch["pull_requests"]:
        pr = ledger["pr"]
        filtered = ledger["filtered"]
        lines.extend((
            f"## [{pr['repo']}#{pr['number']}]({pr['url']}) {html.escape(pr['title'])}",
            f"Head `{pr['headRefOid']}` · {pr['baseRefName']} ← {pr['headRefName']}",
            f"{len(ledger['items'])} entries. Filtered {filtered['review_comments']} review comments in "
            f"{filtered['threads']} threads ({filtered['resolved']} resolved, "
            f"{filtered['outdated']} outdated, counts may overlap).",
            "",
        ))
        for item in ledger["items"]:
            label = item["kind"].replace("_", " ")
            display = [str(item["id"])]
            display.extend(str(item[key]) for key in (
                "author", "name", "severity", "state", "commit_id", "status", "conclusion", "level",
            ) if item.get(key))
            if item.get("path"):
                location = item["path"]
                if item.get("line") is not None:
                    location += f":{item['line']}"
                    if item.get("end_line") not in (None, item["line"]):
                        location += f"–{item['end_line']}"
                display.append(location)
            if "thread" in item:
                thread = item["thread"]
                flags = [name for flag, name in (("isResolved", "resolved"), ("isOutdated", "outdated"))
                         if thread[flag]]
                display.append(f"thread {thread['id']} ({', '.join(flags) or 'open'})")
                if item["reply_to"] is not None:
                    display.append(f"reply to {item['reply_to']}")
            if item.get("aggregate"):
                display.append("aggregate context")
            lines.append(f"- [{label}]({item['url']}) · " + " · ".join(html.escape(value) for value in display))
            if item.get("title"):
                lines.append("  " + html.escape(item["title"]).replace("\n", "\n  "))
            if item.get("also_seen_in"):
                sources = ", ".join(f"[{source['id']}]({source['url']})" for source in item["also_seen_in"])
                lines.append(f"  Also seen in {sources}")
            if item["body"]:
                lines.extend("  > " + html.escape(line) for line in item["body"].splitlines())
        lines.append("")
    return "\n".join(lines) if lines else "No open pull requests."


def main(argv=None, github=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prs", nargs="*", metavar="PR", help="PR number or HTTPS GitHub PR URL")
    parser.add_argument("--all-open", action="store_true", help="all open PRs in the current repository")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--include-resolved", action="store_true", help="include resolved and outdated threads")
    args = parser.parse_args(argv)
    if bool(args.prs) == args.all_open:
        parser.error("provide one or more PR numbers/URLs or --all-open")
    try:
        batch = collect_batch(github or GitHub(), args.prs, args.all_open, args.include_resolved)
    except (LedgerError, KeyError, TypeError, ValueError) as error:
        print(f"Review ledger unavailable: {error}", file=sys.stderr)
        return 1
    print(json.dumps(batch, ensure_ascii=False, separators=(",", ":"))
          if args.format == "json" else render_markdown(batch).rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
