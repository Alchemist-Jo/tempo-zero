"""Write the two main result tables of the paper into index.html.

Rows are parsed from sections/05-experiments.tex of the manuscript, including
the Gemma blocks that main.tex builds, so every number matches the paper.

    python3 build_tables.py <experiments.tex> <index.html>
"""
import re
import sys
from pathlib import Path

TEX, PAGE = Path(sys.argv[1]), Path(sys.argv[2])
BACKBONES = {"4B": "Qwen3-VL-4B", "8B": "Qwen3-VL-8B", "30B-A3B": "Qwen3-VL-30B-A3B", "Gemma": "Gemma 4 E4B"}
TABLES = {
    "grounding": {
        "columns": list(range(15)),
        "groups": [("ANet-RTL", 4), ("ActivityNet Captions", 4), ("Charades-STA", 4), ("NExT-GQA", 2), ("", 1)],
        "metrics": ["mIoU", "R@0.3", "R@0.5", "R@0.7"] * 3 + ["GQA@0.3", "GQA@0.5", "Avg."],
    },
    "qa": {
        "columns": list(range(9)),
        "groups": [("Long-video understanding", 4), ("Video reasoning", 4), ("", 1)],
        "metrics": ["LongVideoBench", "MLVU", "Video-MME-Long", "LSDBench",
                    "LongVideoReason", "MMVU", "VideoMathQA", "VideoMMMU", "Avg."],
    },
}


def cell(raw):
    """One LaTeX cell as HTML: value, best/second mark and delta over the base model."""
    raw = raw.strip()
    delta = ""
    match = re.fullmatch(r"\\withdelta\{(.*)\}\{\\(up|down)\{([\d.]+)\}\}", raw)
    if match:
        raw, sign, amount = match.groups()
        delta = f'<span class="d {sign}">{"+" if sign == "up" else "−"}{amount}</span>'
    mark = re.fullmatch(r"\\(best|second)\{([\d.]+)\}", raw)
    value, cls = (mark.group(2), f' class="{mark.group(1)}"') if mark else (raw, "")
    return f'<td{cls}><span class="v">{value}</span>{delta}</td>'


def rows(label):
    """(backbone, method, cells) for every row of the table with this label."""
    text = TEX.read_text()
    start = text.index(rf"\label{{tab:{label}}}")
    body = text[text.index(r"\midrule", start):text.index(r"\bottomrule", start)]
    block = []
    for line in body.splitlines():
        line = line.strip().removesuffix(r"\\").strip()
        if not (line.startswith("&") or line.startswith(r"\ourrow")):
            continue
        parts = [part.strip() for part in line.split("&")]
        name = re.search(r"\\textit\{([^}]*)\}(?:\\\\\\textit\{([^}]*)\})?", parts[0])
        method = "Tempo-Zero" if parts[1] == r"\method{}" else parts[1]
        block.append((method, parts[2:]))
        if name:
            yield BACKBONES["".join(g for g in name.groups() if g)], block
            block = []


def table(label):
    spec = TABLES[label]
    head = "".join(f'<th colspan="{span}">{group}</th>' for group, span in spec["groups"])
    metrics = "".join(f"<th>{metric}</th>" for metric in spec["metrics"])
    out = [f'<table class="results"><thead><tr><th rowspan="2">Backbone</th><th rowspan="2">Method</th>{head}</tr>',
           f"<tr>{metrics}</tr></thead>"]
    for backbone, block in rows(label):
        out.append("<tbody>")
        for index, (method, cells) in enumerate(block):
            first = f'<th rowspan="{len(block)}" class="bb">{backbone}</th>' if index == 0 else ""
            ours = ' class="ours"' if method == "Tempo-Zero" else ""
            values = "".join(cell(cells[column]) for column in spec["columns"])
            out.append(f"<tr{ours}>{first}<td class=\"m\">{method}</td>{values}</tr>")
        out.append("</tbody>")
    out.append("</table>")
    return "\n".join(out)


page = PAGE.read_text()
for label in TABLES:
    page = re.sub(rf"(<!-- table:{label} -->).*?(<!-- /table:{label} -->)",
                  lambda m: f"{m.group(1)}\n{table(label)}\n{m.group(2)}", page, flags=re.S)
PAGE.write_text(page)
