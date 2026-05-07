#!/usr/bin/env python3
"""
ELK API Client — Elasticsearch log querying tool.

Usage:
  python elk_api.py <command> [options]

Commands:
  search     Search logs with DSL query
  trace      Find all logs by traceId
  indices    List available indices
  mapping    Get field mappings for an index
  count      Count matching documents
"""

import sys
import json
import argparse
import os
import base64
import ssl
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin, urlencode


def load_config():
    config_path = os.path.expanduser("~/.claude/skill_config_elk.yml")
    if not os.path.exists(config_path):
        return None
    # Minimal YAML parser for our simple config structure
    # Supports: key: value, nested with indentation, lists with -
    config = {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        config = parse_simple_yaml(content)
    except Exception as e:
        print(json.dumps({"error": f"Failed to load config: {e}"}))
        sys.exit(1)
    return config


def parse_simple_yaml(content):
    """Very minimal YAML parser for our config format."""
    result = {}
    # Each stack entry: (object, key_in_parent)
    stack = [(result, None)]
    indent_stack = [-1]

    for line in content.splitlines():
        raw = line.rstrip()
        if not raw or raw.lstrip().startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip())
        stripped = raw.lstrip()

        # Pop stack for dedent
        while indent <= indent_stack[-1]:
            stack.pop()
            indent_stack.pop()

        current, current_key = stack[-1]

        if stripped.startswith("- "):
            # List item
            val = stripped[2:].strip()
            if " #" in val:
                val = val[:val.index(" #")].strip()
            val = val.strip('"').strip("'")
            if isinstance(current, list):
                current.append(val)
            elif isinstance(current, dict) and len(stack) >= 2:
                # First list item under a key — convert placeholder dict to list
                parent_obj, _ = stack[-2]
                new_list = [val]
                if isinstance(parent_obj, dict) and current_key is not None:
                    parent_obj[current_key] = new_list
                stack[-1] = (new_list, current_key)
            continue

        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value and " #" in value:
                value = value[:value.index(" #")].strip()
            value = value.strip('"').strip("'")

            if not value:
                new_obj = {}
                if isinstance(current, dict):
                    current[key] = new_obj
                stack.append((new_obj, key))
                indent_stack.append(indent)
            else:
                if isinstance(current, dict):
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    current[key] = value

    return result


class ESClient:
    def __init__(self, uri, username=None, password=None, verify_ssl=True):
        self.uri = uri.rstrip("/")
        self.auth = None
        if username and password:
            creds = base64.b64encode(f"{username}:{password}".encode()).decode()
            self.auth = f"Basic {creds}"
        self.verify_ssl = verify_ssl

    def _request(self, method, path, body=None):
        url = f"{self.uri}/{path.lstrip('/')}"
        data = json.dumps(body).encode() if body else None
        headers = {"Content-Type": "application/json"}
        if self.auth:
            headers["Authorization"] = self.auth

        req = Request(url, data=data, headers=headers, method=method)
        ssl_ctx = None
        if not self.verify_ssl:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
        try:
            with urlopen(req, timeout=30, context=ssl_ctx) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            body = e.read().decode()
            try:
                err = json.loads(body)
            except Exception:
                err = {"raw": body}
            return {"error": {"status": e.code, "reason": err}}
        except URLError as e:
            return {"error": {"reason": str(e.reason)}}

    def search(self, index, query_dsl, source_fields=None, size=100, sort=None, sort_order="desc"):
        body = {"query": query_dsl, "size": size}
        if source_fields:
            body["_source"] = source_fields
        if sort:
            body["sort"] = sort
        else:
            body["sort"] = [{"@timestamp": {"order": sort_order}}]
        return self._request("POST", f"/{index}/_search", body)

    def count(self, index, query_dsl):
        body = {"query": query_dsl}
        return self._request("POST", f"/{index}/_count", body)

    def indices(self, pattern="*"):
        result = self._request("GET", f"/_cat/indices/{pattern}?format=json&h=index,health,status,docs.count,store.size&s=index")
        return result

    def mapping(self, index):
        return self._request("GET", f"/{index}/_mapping")

    def scroll_search(self, index, query_dsl, source_fields=None, size=500, max_results=5000):
        """Scroll through large result sets."""
        body = {"query": query_dsl, "size": size}
        if source_fields:
            body["_source"] = source_fields
        body["sort"] = [{"@timestamp": {"order": "asc"}}]

        resp = self._request("POST", f"/{index}/_search?scroll=2m", body)
        if "error" in resp:
            return resp

        hits = resp.get("hits", {}).get("hits", [])
        scroll_id = resp.get("_scroll_id")
        total = resp.get("hits", {}).get("total", {})
        if isinstance(total, dict):
            total = total.get("value", 0)

        all_hits = list(hits)

        while scroll_id and len(hits) > 0 and len(all_hits) < max_results:
            scroll_body = {"scroll": "2m", "scroll_id": scroll_id}
            resp = self._request("POST", "/_search/scroll", scroll_body)
            if "error" in resp:
                break
            hits = resp.get("hits", {}).get("hits", [])
            scroll_id = resp.get("_scroll_id")
            all_hits.extend(hits)

        # Clean up scroll context
        if scroll_id:
            self._request("DELETE", "/_search/scroll", {"scroll_id": scroll_id})

        return {
            "hits": {"total": {"value": total}, "hits": all_hits},
            "_scrolled": True
        }


def build_client_from_config(config, connection_name="default"):
    conns = config.get("connections", {})
    conn = conns.get(connection_name, conns.get("default", {}))
    if not conn:
        print(json.dumps({"error": "No connection config found"}))
        sys.exit(1)
    return ESClient(
        uri=conn.get("uri", ""),
        username=conn.get("username"),
        password=conn.get("password"),
        verify_ssl=conn.get("verify_ssl", True)
    )


def format_hits(resp, fields=None):
    """Extract and format hits from ES response."""
    if "error" in resp:
        return resp

    hits = resp.get("hits", {})
    total = hits.get("total", {})
    if isinstance(total, dict):
        total_value = total.get("value", 0)
    else:
        total_value = total

    results = []
    for hit in hits.get("hits", []):
        src = hit.get("_source", {})
        record = {
            "_id": hit.get("_id"),
            "_index": hit.get("_index"),
        }
        if fields:
            for f in fields:
                # Support nested fields like "host.name"
                if "." in f:
                    parts = f.split(".")
                    val = src
                    for p in parts:
                        val = val.get(p, {}) if isinstance(val, dict) else None
                    record[f] = val
                else:
                    record[f] = src.get(f)
        else:
            record.update(src)
        results.append(record)

    return {
        "total": total_value,
        "returned": len(results),
        "hits": results
    }


def cmd_search(args, client):
    # Parse query DSL from --query (JSON string) or --text (full-text)
    if args.query:
        try:
            query_dsl = json.loads(args.query)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid query JSON: {e}"}))
            sys.exit(1)
    elif args.text:
        query_dsl = {
            "multi_match": {
                "query": args.text,
                "fields": ["message", "logger", "thread", "codeline"],
                "type": "phrase"
            }
        }
    else:
        query_dsl = {"match_all": {}}

    # Add time range filter
    if args.time_from or args.time_to:
        time_filter = {"range": {"@timestamp": {}}}
        if args.time_from:
            time_filter["range"]["@timestamp"]["gte"] = args.time_from
        if args.time_to:
            time_filter["range"]["@timestamp"]["lte"] = args.time_to

        if "bool" in query_dsl:
            query_dsl["bool"].setdefault("filter", []).append(time_filter)
        else:
            query_dsl = {"bool": {"must": [query_dsl], "filter": [time_filter]}}

    fields = [f.strip() for f in args.fields.split(",")] if args.fields else None
    size = args.size or 100
    sort_order = args.sort if hasattr(args, "sort") and args.sort else "desc"

    resp = client.search(args.index, query_dsl, source_fields=fields, size=size, sort_order=sort_order)
    print(json.dumps(format_hits(resp, fields), ensure_ascii=False, indent=2))


def cmd_trace(args, client):
    """Find all logs sharing the same traceId."""
    # Cover common traceId field name variants across different log formats
    query_dsl = {
        "bool": {
            "should": [
                {"term": {"traceId": args.traceid}},
                {"term": {"trace": args.traceid}},
                {"term": {"trace_id": args.traceid}},
                {"term": {"traceId.keyword": args.traceid}},
            ],
            "minimum_should_match": 1
        }
    }

    # Add time range if given
    if args.time_from or args.time_to:
        time_filter = {"range": {"@timestamp": {}}}
        if args.time_from:
            time_filter["range"]["@timestamp"]["gte"] = args.time_from
        if args.time_to:
            time_filter["range"]["@timestamp"]["lte"] = args.time_to
        query_dsl = {"bool": {"must": [query_dsl], "filter": [time_filter]}}

    fields = [f.strip() for f in args.fields.split(",")] if args.fields else None

    resp = client.scroll_search(args.index, query_dsl, source_fields=fields, max_results=args.max_results or 2000)
    print(json.dumps(format_hits(resp, fields), ensure_ascii=False, indent=2))


def cmd_indices(args, client):
    pattern = args.pattern or "*"
    resp = client.indices(pattern)
    if isinstance(resp, list):
        # Filter and sort by name
        resp.sort(key=lambda x: x.get("index", ""))
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(resp, ensure_ascii=False, indent=2))


def cmd_mapping(args, client):
    resp = client.mapping(args.index)
    if "error" in resp:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        return

    # Extract field names only for readability
    output = {}
    for index_name, index_data in resp.items():
        mappings = index_data.get("mappings", {})
        props = mappings.get("properties", {})
        output[index_name] = {"fields": list(props.keys())}

    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_aggs(args, client):
    """Run a terms aggregation to count by field value."""
    if args.query:
        try:
            query_dsl = json.loads(args.query)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid query JSON: {e}"}))
            sys.exit(1)
    else:
        query_dsl = {"match_all": {}}

    if args.time_from or args.time_to:
        time_filter = {"range": {"@timestamp": {}}}
        if args.time_from:
            time_filter["range"]["@timestamp"]["gte"] = args.time_from
        if args.time_to:
            time_filter["range"]["@timestamp"]["lte"] = args.time_to
        if "bool" in query_dsl:
            query_dsl["bool"].setdefault("filter", []).append(time_filter)
        else:
            query_dsl = {"bool": {"must": [query_dsl], "filter": [time_filter]}}

    body = {
        "query": query_dsl,
        "size": 0,
        "aggs": {
            "group_by": {
                "terms": {
                    "field": args.field,
                    "size": args.top or 20
                }
            }
        }
    }
    resp = client._request("POST", f"/{args.index}/_search", body)
    if "error" in resp:
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        return

    total = resp.get("hits", {}).get("total", {})
    if isinstance(total, dict):
        total = total.get("value", 0)
    buckets = resp.get("aggregations", {}).get("group_by", {}).get("buckets", [])
    print(json.dumps({
        "total": total,
        "field": args.field,
        "buckets": [{"key": b["key"], "count": b["doc_count"]} for b in buckets]
    }, ensure_ascii=False, indent=2))


def cmd_ping(args, client):
    """Check Elasticsearch cluster health."""
    resp = client._request("GET", "/_cluster/health")
    if "error" in resp:
        print(json.dumps({"status": "error", "detail": resp["error"]}, ensure_ascii=False, indent=2))
        return
    print(json.dumps({
        "status": resp.get("status"),
        "cluster_name": resp.get("cluster_name"),
        "number_of_nodes": resp.get("number_of_nodes"),
        "number_of_data_nodes": resp.get("number_of_data_nodes"),
        "active_shards": resp.get("active_shards"),
        "unassigned_shards": resp.get("unassigned_shards"),
    }, ensure_ascii=False, indent=2))


def cmd_config(args, client=None):
    """Print the user's config file with password fields masked."""
    config_path = os.path.expanduser("~/.claude/skill_config_elk.yml")
    if not os.path.exists(config_path):
        print(json.dumps({"error": f"Config not found: {config_path}"}, ensure_ascii=False))
        return
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.lstrip()
            if stripped.startswith("password:"):
                indent = line[: len(line) - len(stripped)]
                print(f"{indent}password: ***", end="" if line.endswith("\n") else "\n")
                if line.endswith("\n"):
                    print()
            else:
                print(line, end="")


def cmd_count(args, client):
    if args.query:
        try:
            query_dsl = json.loads(args.query)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid query JSON: {e}"}))
            sys.exit(1)
    else:
        query_dsl = {"match_all": {}}

    if args.time_from or args.time_to:
        time_filter = {"range": {"@timestamp": {}}}
        if args.time_from:
            time_filter["range"]["@timestamp"]["gte"] = args.time_from
        if args.time_to:
            time_filter["range"]["@timestamp"]["lte"] = args.time_to
        if "bool" in query_dsl:
            query_dsl["bool"].setdefault("filter", []).append(time_filter)
        else:
            query_dsl = {"bool": {"must": [query_dsl], "filter": [time_filter]}}

    resp = client.count(args.index, query_dsl)
    print(json.dumps(resp, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="ELK API Client")
    parser.add_argument("--uri", help="Elasticsearch URI (overrides config)")
    parser.add_argument("--username", help="ES username (overrides config)")
    parser.add_argument("--password", help="ES password (overrides config)")
    parser.add_argument("--connection", default="default", help="Config connection name")

    subparsers = parser.add_subparsers(dest="command")

    # search command
    sp = subparsers.add_parser("search", help="Search logs")
    sp.add_argument("--index", required=True, help="Index pattern, e.g. logstash-*")
    sp.add_argument("--query", help="ES query DSL as JSON string")
    sp.add_argument("--text", help="Full-text search string")
    sp.add_argument("--fields", help="Comma-separated fields to return")
    sp.add_argument("--from", dest="time_from", help="Start time (ISO8601 or relative like now-1h)")
    sp.add_argument("--to", dest="time_to", help="End time (ISO8601)")
    sp.add_argument("--size", type=int, default=100, help="Number of results (default: 100)")
    sp.add_argument("--sort", choices=["asc", "desc"], default="desc", help="Sort order by @timestamp (default: desc)")

    # trace command
    sp = subparsers.add_parser("trace", help="Find logs by traceId")
    sp.add_argument("--index", required=True, help="Index pattern")
    sp.add_argument("--traceid", required=True, help="traceId value")
    sp.add_argument("--fields", help="Comma-separated fields to return")
    sp.add_argument("--from", dest="time_from", help="Start time")
    sp.add_argument("--to", dest="time_to", help="End time")
    sp.add_argument("--max-results", dest="max_results", type=int, default=2000)

    # indices command
    sp = subparsers.add_parser("indices", help="List indices")
    sp.add_argument("--pattern", default="*", help="Index pattern filter")

    # mapping command
    sp = subparsers.add_parser("mapping", help="Get field mappings")
    sp.add_argument("--index", required=True, help="Index name or pattern")

    # count command
    sp = subparsers.add_parser("count", help="Count matching documents")
    sp.add_argument("--index", required=True, help="Index pattern")
    sp.add_argument("--query", help="ES query DSL as JSON string")
    sp.add_argument("--from", dest="time_from", help="Start time")
    sp.add_argument("--to", dest="time_to", help="End time")

    # aggs command
    sp = subparsers.add_parser("aggs", help="Terms aggregation — count by field value")
    sp.add_argument("--index", required=True, help="Index pattern")
    sp.add_argument("--field", required=True, help="Field to aggregate on (e.g. level, logger)")
    sp.add_argument("--query", help="ES query DSL as JSON string (optional filter)")
    sp.add_argument("--from", dest="time_from", help="Start time")
    sp.add_argument("--to", dest="time_to", help="End time")
    sp.add_argument("--top", type=int, default=20, help="Number of top buckets (default: 20)")

    # ping command
    sp = subparsers.add_parser("ping", help="Check Elasticsearch cluster health")

    # config command — print config file with passwords masked
    sp = subparsers.add_parser("config", help="Print config file with password masked")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # config command does not need an ES client
    if args.command == "config":
        cmd_config(args)
        return

    # Build client
    if args.uri:
        client = ESClient(args.uri, args.username, args.password)
    else:
        config = load_config()
        if not config:
            print(json.dumps({"error": "No config found at ~/.claude/skill_config_elk.yml. Run install.sh first."}))
            sys.exit(1)
        client = build_client_from_config(config, args.connection)

    dispatch = {
        "search": cmd_search,
        "trace": cmd_trace,
        "indices": cmd_indices,
        "mapping": cmd_mapping,
        "count": cmd_count,
        "aggs": cmd_aggs,
        "ping": cmd_ping,
    }

    dispatch[args.command](args, client)


if __name__ == "__main__":
    main()
