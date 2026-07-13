#!/usr/bin/env python3
"""Render a self-contained PR walkthrough from structured JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "pr-walkthrough-template.html"
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def require(mapping: dict[str, Any], key: str, context: str) -> Any:
    value = mapping.get(key)
    if value is None or value == "" or value == []:
        raise ValueError(f"{context}.{key} is required")
    return value


def validate_id(value: str, context: str) -> None:
    if not ID_PATTERN.fullmatch(value):
        raise ValueError(f"{context} must use lowercase kebab-case: {value!r}")


def validate_data(data: dict[str, Any]) -> None:
    meta = require(data, "meta", "root")
    for key in ("title", "source_url", "base", "head", "generated_at", "intent"):
        require(meta, key, "meta")
    if not str(meta["source_url"]).startswith(("https://", "http://")):
        raise ValueError("meta.source_url must use http:// or https://")

    files = require(data, "files", "root")
    layers = require(data, "layers", "root")
    flowchart = require(data, "flowchart", "root")
    nodes = require(flowchart, "nodes", "flowchart")

    layer_ids: set[str] = set()
    for index, layer in enumerate(layers):
        layer_id = require(layer, "id", f"layers[{index}]")
        validate_id(layer_id, f"layers[{index}].id")
        if layer_id in layer_ids:
            raise ValueError(f"duplicate layer id: {layer_id}")
        layer_ids.add(layer_id)
        for key in ("label", "title", "purpose", "changed_behavior", "contract", "interaction", "reviewer_focus"):
            require(layer, key, f"layers[{index}]")
        snippets = layer.get("snippets", [])
        if not snippets and not layer.get("no_snippet_reason"):
            raise ValueError(f"layers[{index}] needs snippets or no_snippet_reason")

    file_ids: set[str] = set()
    file_paths: set[str] = set()
    for index, file_data in enumerate(files):
        file_id = require(file_data, "id", f"files[{index}]")
        validate_id(file_id, f"files[{index}].id")
        if file_id in file_ids:
            raise ValueError(f"duplicate file id: {file_id}")
        file_ids.add(file_id)
        file_path = require(file_data, "path", f"files[{index}]")
        if file_path in file_paths:
            raise ValueError(f"duplicate file path: {file_path}")
        file_paths.add(file_path)
        if require(file_data, "layer_id", f"files[{index}]") not in layer_ids:
            raise ValueError(f"files[{index}].layer_id does not match a layer")
        for key in ("role", "change", "interactions", "evidence"):
            require(file_data, key, f"files[{index}]")

    node_ids: set[str] = set()
    valid_targets = {f"file-{value}" for value in file_ids} | {
        f"layer-{value}" for value in layer_ids
    }
    for index, node in enumerate(nodes):
        node_id = require(node, "id", f"flowchart.nodes[{index}]")
        validate_id(node_id, f"flowchart.nodes[{index}].id")
        if node_id in node_ids:
            raise ValueError(f"duplicate flowchart node id: {node_id}")
        node_ids.add(node_id)
        require(node, "label", f"flowchart.nodes[{index}]")
        if len(str(node["label"])) > 30:
            raise ValueError(f"flowchart.nodes[{index}].label must be 30 characters or fewer")
        if len(str(node.get("detail", ""))) > 38:
            raise ValueError(f"flowchart.nodes[{index}].detail must be 38 characters or fewer")
        if require(node, "target", f"flowchart.nodes[{index}]") not in valid_targets:
            raise ValueError(f"flowchart.nodes[{index}].target does not match a file or layer")
        for key in ("column", "row"):
            value = require(node, key, f"flowchart.nodes[{index}]")
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"flowchart.nodes[{index}].{key} must be a non-negative integer")

    for index, edge in enumerate(flowchart.get("edges", [])):
        if require(edge, "from", f"flowchart.edges[{index}]") not in node_ids:
            raise ValueError(f"flowchart.edges[{index}].from does not match a node")
        if require(edge, "to", f"flowchart.edges[{index}]") not in node_ids:
            raise ValueError(f"flowchart.edges[{index}].to does not match a node")
        require(edge, "label", f"flowchart.edges[{index}]")
        require(edge, "evidence", f"flowchart.edges[{index}]")
        confidence = require(edge, "confidence", f"flowchart.edges[{index}]")
        if confidence not in {"high", "medium", "low"}:
            raise ValueError(f"flowchart.edges[{index}].confidence must be high, medium, or low")

    node_targets = {node["target"] for node in nodes}
    for index, file_data in enumerate(files):
        if (
            f"file-{file_data['id']}" not in node_targets
            and f"layer-{file_data['layer_id']}" not in node_targets
        ):
            raise ValueError(f"files[{index}] is missing from the flowchart")


def list_items(items: list[str], empty_message: str) -> str:
    if not items:
        return f'<li class="empty-state">{escape(empty_message)}</li>'
    return "\n".join(f"<li>{escape(item)}</li>" for item in items)


def render_file_rows(files: list[dict[str, Any]], layers_by_id: dict[str, dict[str, Any]]) -> str:
    rows: list[str] = []
    for file_data in files:
        file_id = escape(file_data["id"])
        layer = layers_by_id[file_data["layer_id"]]
        risks = file_data.get("risks", [])
        risk_markup = "".join(
            f'<span class="tag tag-risk">{escape(risk)}</span>' for risk in risks
        ) or '<span class="tag">None noted</span>'
        search_text = " ".join(
            str(file_data.get(key, ""))
            for key in ("path", "role", "change", "interactions", "evidence")
        )
        rows.append(
            f"""
            <tr id="file-{file_id}" data-file-id="{file_id}" data-layer="{escape(file_data['layer_id'])}" data-layer-label="{escape(layer['label'])}" data-search="{escape(search_text.lower())}">
              <th scope="row" class="file-path-cell"><a href="#layer-{escape(layer['id'])}" class="path-link">{escape(file_data['path'])}</a></th>
              <td><span class="layer-label">{escape(layer['label'])}</span></td>
              <td>{escape(file_data['role'])}</td>
              <td>{escape(file_data['change'])}</td>
              <td>{escape(file_data['interactions'])}</td>
              <td>{escape(file_data['evidence'])}</td>
              <td><div class="tag-list">{risk_markup}</div></td>
            </tr>"""
        )
    return "\n".join(rows)


def render_snippet(snippet: dict[str, Any]) -> str:
    path = require(snippet, "path", "snippet")
    code = require(snippet, "code", "snippet")
    start_line = snippet.get("start_line")
    end_line = snippet.get("end_line")
    if start_line and end_line and start_line != end_line:
        line_label = f"{start_line}-{end_line}"
    elif start_line:
        line_label = str(start_line)
    else:
        line_label = "changed lines"
    language = escape(snippet.get("language", "text"))
    return f"""
      <figure class="code-snippet">
        <figcaption><span class="snippet-path">{escape(path)}</span><span class="snippet-lines">Lines {escape(line_label)}</span></figcaption>
        <pre tabindex="0" aria-label="Code from {escape(path)}, {escape(line_label)}"><code data-language="{language}">{escape(code)}</code></pre>
      </figure>"""


def render_layers(layers: list[dict[str, Any]], files_by_layer: dict[str, list[dict[str, Any]]]) -> str:
    sections: list[str] = []
    for index, layer in enumerate(layers, start=1):
        layer_files = files_by_layer.get(layer["id"], [])
        file_links = ", ".join(
            f'<a href="#file-{escape(file_data["id"])}" class="path-link">{escape(file_data["path"])}</a>'
            for file_data in layer_files
        ) or "No touched file assigned"
        snippets = "\n".join(render_snippet(item) for item in layer.get("snippets", []))
        if not snippets:
            snippets = f'<p class="empty-state">{escape(layer["no_snippet_reason"])}</p>'
        sections.append(
            f"""
        <details class="layer" id="layer-{escape(layer['id'])}" data-layer-id="{escape(layer['id'])}" open>
          <summary>
            <span class="step-number">{index}</span>
            <span><span class="eyebrow">{escape(layer['label'])}</span><span class="summary-title">{escape(layer['title'])}</span></span>
          </summary>
          <div class="layer-body">
            <dl class="layer-contract">
              <div><dt>Purpose</dt><dd>{escape(layer['purpose'])}</dd></div>
              <div><dt>Files</dt><dd>{file_links}</dd></div>
              <div><dt>Changed Behavior</dt><dd>{escape(layer['changed_behavior'])}</dd></div>
              <div><dt>Contract</dt><dd>{escape(layer['contract'])}</dd></div>
              <div><dt>Interaction</dt><dd>{escape(layer['interaction'])}</dd></div>
              <div><dt>Reviewer Focus</dt><dd>{escape(layer['reviewer_focus'])}</dd></div>
            </dl>
            <div class="snippet-stack">{snippets}</div>
          </div>
        </details>"""
        )
    return "\n".join(sections)


def render_flowchart(flowchart: dict[str, Any]) -> str:
    nodes = flowchart["nodes"]
    node_width = 232
    node_height = 82
    column_gap = 86
    row_gap = 56
    margin_x = 34
    margin_y = 42
    positioned: dict[str, dict[str, Any]] = {}
    for node in nodes:
        positioned[node["id"]] = {
            **node,
            "x": margin_x + node["column"] * (node_width + column_gap),
            "y": margin_y + node["row"] * (node_height + row_gap),
        }
    max_column = max(node["column"] for node in nodes)
    max_row = max(node["row"] for node in nodes)
    width = margin_x * 2 + node_width + max_column * (node_width + column_gap)
    height = margin_y * 2 + node_height + max_row * (node_height + row_gap)

    edges: list[str] = []
    for edge in flowchart.get("edges", []):
        source = positioned[edge["from"]]
        target = positioned[edge["to"]]
        if source["column"] == target["column"]:
            x1 = source["x"] + node_width / 2
            y1 = source["y"] + node_height
            x2 = target["x"] + node_width / 2
            y2 = target["y"]
            bend = (y1 + y2) / 2
            path = f"M{x1:g} {y1:g} C{x1:g} {bend:g} {x2:g} {bend:g} {x2:g} {y2:g}"
        else:
            x1 = source["x"] + node_width
            y1 = source["y"] + node_height / 2
            x2 = target["x"]
            y2 = target["y"] + node_height / 2
            bend = (x1 + x2) / 2
            path = f"M{x1:g} {y1:g} C{bend:g} {y1:g} {bend:g} {y2:g} {x2:g} {y2:g}"
        label_x = (x1 + x2) / 2
        label_y = (y1 + y2) / 2 - 8
        inferred_class = " is-inferred" if edge.get("inferred") else ""
        inferred_label = " (inferred)" if edge.get("inferred") else ""
        edges.append(
            f"""
          <g class="flow-edge{inferred_class}" data-from="{escape(edge['from'])}" data-to="{escape(edge['to'])}">
            <path d="{path}" marker-end="url(#arrowhead)"><title>{escape(edge['evidence'])} Confidence: {escape(edge['confidence'])}.</title></path>
            <text x="{label_x:g}" y="{label_y:g}" text-anchor="middle">{escape(edge['label'])}{inferred_label}</text>
          </g>"""
        )

    node_markup: list[str] = []
    for node in nodes:
        item = positioned[node["id"]]
        detail = escape(node.get("detail", ""))
        node_markup.append(
            f"""
          <a href="#{escape(node['target'])}" class="flow-node-link" data-node-id="{escape(node['id'])}" data-target="{escape(node['target'])}" aria-label="{escape(node['label'])}. {detail}">
            <g class="flow-node flow-node-{escape(node.get('kind', 'default'))}" transform="translate({item['x']} {item['y']})">
              <rect width="{node_width}" height="{node_height}" rx="6"></rect>
              <text x="16" y="30" class="flow-node-title">{escape(node['label'])}</text>
              <text x="16" y="55" class="flow-node-detail">{detail}</text>
            </g>
          </a>"""
        )

    return f"""
      <svg class="flowchart" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="flowchart-title flowchart-description">
        <title id="flowchart-title">Changed file connection flowchart</title>
        <desc id="flowchart-description">{escape(flowchart.get('description', 'Execution, data, configuration, and test relationships between changed files.'))}</desc>
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
            <path d="M0,0 L10,4 L0,8 Z"></path>
          </marker>
        </defs>
        <g class="flow-edges">{''.join(edges)}</g>
        <g class="flow-nodes">{''.join(node_markup)}</g>
      </svg>"""


def render(data: dict[str, Any], template: str) -> str:
    validate_data(data)
    meta = data["meta"]
    files = data["files"]
    layers = data["layers"]
    layers_by_id = {layer["id"]: layer for layer in layers}
    files_by_layer: dict[str, list[dict[str, Any]]] = {}
    for file_data in files:
        files_by_layer.setdefault(file_data["layer_id"], []).append(file_data)

    risks = sorted({risk for file_data in files for risk in file_data.get("risks", [])})
    layer_counts = [
        f"{layer['label']} {len(files_by_layer.get(layer['id'], []))}"
        for layer in layers
    ]
    risk_counts = [
        f"{risk} {sum(risk in file_data.get('risks', []) for file_data in files)}"
        for risk in risks
    ]
    summary = data.get("summary", {})
    additions = summary.get("additions", 0)
    deletions = summary.get("deletions", 0)
    source_url = escape(meta["source_url"])
    author = escape(meta.get("author", "Unavailable"))
    head_oid = escape(meta.get("head_oid", "Unavailable"))
    overview = "\n".join(f"<p>{escape(paragraph)}</p>" for paragraph in data.get("overview", []))
    if not overview:
        overview = '<p class="empty-state">No overview was provided.</p>'

    markdown_summary = data.get("markdown_summary") or (
        f"{meta['title']}\n\n"
        f"Intent: {meta['intent']}\n"
        f"Files: {len(files)} changed, +{additions}/-{deletions}.\n"
        f"Layers: {' -> '.join(layer['label'] for layer in layers)}\n"
        f"Source: {meta['source_url']}"
    )

    replacements = {
        "PAGE_TITLE": escape(meta["title"]),
        "SOURCE_LINK": f'<a href="{source_url}" target="_blank" rel="noreferrer">{source_url}</a>',
        "BASE": escape(meta["base"]),
        "HEAD": escape(meta["head"]),
        "HEAD_OID": head_oid,
        "AUTHOR": author,
        "GENERATED_AT": escape(meta["generated_at"]),
        "INTENT": escape(meta["intent"]),
        "FILE_COUNT": str(len(files)),
        "LAYER_COUNT": str(len(layers)),
        "LAYER_BREAKDOWN": escape(", ".join(layer_counts)),
        "ADDITIONS": escape(additions),
        "DELETIONS": escape(deletions),
        "RISK_COUNT": str(len(risks)),
        "RISK_BREAKDOWN": escape(", ".join(risk_counts) if risk_counts else "None noted"),
        "EXECUTION_RANGE": escape(f"{layers[0]['label']} to {layers[-1]['label']}"),
        "LAYER_OPTIONS": "\n".join(
            f'<option value="{escape(layer["id"])}">{escape(layer["label"])}</option>'
            for layer in layers
        ),
        "OVERVIEW_PARAGRAPHS": overview,
        "FILE_ROWS": render_file_rows(files, layers_by_id),
        "FLOWCHART": render_flowchart(data["flowchart"]),
        "LAYER_DETAILS": render_layers(layers, files_by_layer),
        "VALIDATION_ITEMS": list_items(data.get("evidence", {}).get("validation", []), "No validation evidence was available."),
        "SOURCE_ITEMS": list_items(data.get("evidence", {}).get("sources", []), "No command sources were recorded."),
        "UNKNOWNS": list_items(data.get("unknowns", []), "No unknowns or assumptions were recorded."),
        "PROVENANCE_ITEMS": list_items(data.get("provenance", []), "No provenance was recorded."),
        "MARKDOWN_SUMMARY": json.dumps(markdown_summary).replace("</", "<\\/"),
    }
    output = template
    for key, value in replacements.items():
        output = output.replace(f"@@{key}@@", value)
    unresolved = sorted(set(re.findall(r"@@[A-Z0-9_]+@@", output)))
    if unresolved:
        raise ValueError(f"unresolved template tokens: {', '.join(unresolved)}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Walkthrough JSON data")
    parser.add_argument("--output", required=True, type=Path, help="Rendered HTML path")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="HTML template override")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    template = args.template.read_text(encoding="utf-8")
    output = render(data, template)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Rendered {len(data['files'])} files across {len(data['layers'])} layers: {args.output}")


if __name__ == "__main__":
    main()
