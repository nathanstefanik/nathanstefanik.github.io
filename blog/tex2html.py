#!/usr/bin/env python3
"""Minimal LaTeX-article renderer for blog posts.

Targets the subset these posts use: section/subsection, amsthm environments
sharing one counter, proofs, label/ref, emph, and math.
Math ($...$, $$...$$, align*) is passed through verbatim for MathJax.

Usage: python3 tex2html.py input.tex [output.html]
"""

import re
import sys
from pathlib import Path

ENV = {
    "theorem": "Theorem",
    "lemma": "Lemma",
    "proposition": "Proposition",
    "corollary": "Corollary",
    "definition": "Definition",
    "remark": "Remark",
}


def tex_to_html(src):
    title = (re.search(r"\\title\{([^}]*)\}", src) or [None, ""])[1].strip()
    body = src.split("\\begin{document}")[1].split("\\end{document}")[0]
    body = re.sub(r"(^|[^\\])%.*$", r"\1", body, flags=re.M)
    body = body.replace("\\maketitle", "")

    math = []

    def stash(tex) -> str:
        if hasattr(tex, "group"):
            tex = tex.group(0)
        math.append(re.sub(r"\s*\\qedhere", "", tex))
        return f"\0{len(math) - 1}\0"

    body = re.sub(r"\\begin\{align\*\}[\s\S]*?\\end\{align\*\}", stash, body)
    body = re.sub(r"\$\$[\s\S]*?\$\$", stash, body)
    body = re.sub(r"\$([^$]+)\$", lambda m: stash(f"\\({m.group(1)}\\)"), body)

    def para(text):
        return "</p>\n<p>".join(p.strip() for p in text.strip().split("\n\n") if p.strip())

    body = re.sub(
        r"\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}",
        lambda m: f'<div class="abstract"><p><strong>Abstract.</strong> {para(m.group(1))}</p></div>',
        body,
    )

    labels = {}
    n = 0

    def env_repl(m):
        nonlocal n
        n += 1
        env, name, inner = m.group(1), m.group(2), m.group(3)
        id_attr = ""

        def label_repl(lm):
            nonlocal id_attr
            labels[lm.group(1)] = n
            id_attr = f' id="{lm.group(1)}"'
            return ""

        inner = re.sub(r"\\label\{([^}]*)\}", label_repl, inner, count=1)
        head = f"{ENV[env]} {n}" + (f" ({name})" if name else "") + "."
        return f'<div class="env {env}"{id_attr}><p><strong>{head}</strong> {para(inner)}</p></div>'

    body = re.sub(
        r"\\begin\{(theorem|lemma|proposition|corollary|definition|remark)\}(?:\[([^\]]*)\])?([\s\S]*?)\\end\{\1\}",
        env_repl,
        body,
    )

    body = re.sub(
        r"\\begin\{proof\}([\s\S]*?)\\end\{proof\}",
        lambda m: f'<div class="proof"><p><em>Proof.</em> {para(m.group(1))} <span class="qed"></span></p></div>',
        body,
    )

    sec = sub = 0

    def section_repl(m):
        nonlocal sec, sub
        if m.group(1):
            sub += 1
            return f"<h3>{sec}.{sub}&ensp;{m.group(2)}</h3>\n"
        sub = 0
        sec += 1
        return f"<h2>{sec}&ensp;{m.group(2)}</h2>\n"

    body = re.sub(r"\\(sub)?section\{([^}]*)\}", section_repl, body)
    body = re.sub(r"\\emph\{([^}]*)\}", r"<em>\1</em>", body)
    body = re.sub(
        r"\\ref\{([^}]*)\}",
        lambda m: f'<a href="#{m.group(1)}">{labels.get(m.group(1), "?")}</a>',
        body,
    )
    body = body.replace("~", "&nbsp;")

    chunks = [
        chunk if chunk.startswith("<") else f"<p>{chunk}</p>"
        for chunk in (c.strip() for c in body.split("\n\n"))
        if chunk
    ]
    html = "\n".join(chunks)
    html = re.sub(r"\0(\d+)\0", lambda m: math[int(m.group(1))], html)
    plain_title = re.sub(r"\$([^$]+)\$", r"\1", title)
    return title, plain_title, html


def title_html(title):
    return re.sub(r"\$([^$]+)\$", r"\\(\1\\)", title)


def page_html(title, plain_title, html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' https: data:; frame-src 'self'; base-uri 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline';">
  <title>{plain_title}</title>
  <link rel="stylesheet" type="text/css" href="/html/pagestyle.css">
  <script>
    MathJax = {{
      tex: {{
        inlineMath: [['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
      }}
    }};
  </script>
  <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
  <style>
    .abstract {{ margin: 1.5em 0; padding-left: 1em; border-left: 3px solid #888; }}
    .env {{ margin: 1.25em 0; }}
    .proof {{ margin: 0.75em 0 1.25em 1em; padding-left: 0.75em; border-left: 2px solid #ccc; display: flow-root; }}
    .proof .qed {{ float: right; display: inline-block; width: 0.55em; height: 0.55em; border: 1px solid #000; background: #fff; }}
    mjx-container {{ overflow-x: auto; overflow-y: hidden; }}
  </style>
</head>
<body>
<nav class="navigation">
  <ul>
    <li><a href="/"> Home </a></li>
    <li><a href="/cv/"> CV </a></li>
    <li><a href="/blog/"> Blog </a></li>
    <li><a href="/projects/"> Projects </a></li>
    <li><a href="/photos/"> Photos </a></li>
    <li><a href="https://showtimes.nathanstefanik.xyz"> Showtimes </a></li>
  </ul>
</nav>

<article>
<h1>{title_html(title)}</h1>
{html}
</article>

</body>
</html>
"""


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: python3 tex2html.py input.tex [output.html]\n")
        sys.exit(1)
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix(".html")
    title, plain_title, html = tex_to_html(input_path.read_text())
    output_path.write_text(page_html(title, plain_title, html))


if __name__ == "__main__":
    main()
