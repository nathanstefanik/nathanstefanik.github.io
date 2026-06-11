/* Minimal LaTeX-article renderer.
   Targets the subset these posts use: \section/\subsection, amsthm
   environments sharing one counter, proofs, \label/\ref, \emph, and math.
   Math ($...$, $$...$$, align*) is passed through verbatim for MathJax. */

const ENV = {
  theorem: "Theorem",
  lemma: "Lemma",
  proposition: "Proposition",
  corollary: "Corollary",
  definition: "Definition",
  remark: "Remark",
};

function texToHtml(src) {
  const title = (src.match(/\\title\{([^}]*)\}/)?.[1] ?? "").trim();
  let body = src.split("\\begin{document}")[1].split("\\end{document}")[0];
  body = body.replace(/(^|[^\\])%.*$/gm, "$1");
  body = body.replace(/\\maketitle/, "");

  // stash math so the text transforms below cannot touch it; restored at the end
  const math = [];
  const stash = (tex) => `\u0000${math.push(tex.replace(/\s*\\qedhere/g, "")) - 1}\u0000`;
  body = body
    .replace(/\\begin\{align\*\}[\s\S]*?\\end\{align\*\}/g, stash)
    .replace(/\$\$[\s\S]*?\$\$/g, stash)
    .replace(/\$([^$]+)\$/g, (_, tex) => stash(`\\(${tex}\\)`));

  const para = (text) =>
    text.trim().split(/\n\s*\n/).map((p) => p.trim()).join("</p>\n<p>");

  body = body.replace(
    /\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}/g,
    (_, inner) =>
      `<div class="abstract"><p><strong>Abstract.</strong> ${para(inner)}</p></div>`
  );

  // amsthm environments share one counter, mirroring the preamble's \newtheorem setup
  const labels = {};
  let n = 0;
  body = body.replace(
    /\\begin\{(theorem|lemma|proposition|corollary|definition|remark)\}(?:\[([^\]]*)\])?([\s\S]*?)\\end\{\1\}/g,
    (_, env, name, inner) => {
      n++;
      let id = "";
      inner = inner.replace(/\\label\{([^}]*)\}/, (_, key) => {
        labels[key] = n;
        id = ` id="${key}"`;
        return "";
      });
      const head = `${ENV[env]} ${n}${name ? ` (${name})` : ""}.`;
      return `<div class="env ${env}"${id}><p><strong>${head}</strong> ${para(inner)}</p></div>`;
    }
  );

  body = body.replace(
    /\\begin\{proof\}([\s\S]*?)\\end\{proof\}/g,
    (_, inner) =>
      `<div class="proof"><p><em>Proof.</em> ${para(inner)} <span class="qed">&#8718;</span></p></div>`
  );

  let sec = 0;
  let sub = 0;
  // trailing newline gives headings their own chunk even when text follows on the next line
  body = body.replace(/\\(sub)?section\{([^}]*)\}/g, (_, isSub, text) =>
    isSub
      ? `<h3>${sec}.${++sub}&ensp;${text}</h3>\n`
      : ((sub = 0), `<h2>${++sec}&ensp;${text}</h2>\n`)
  );

  body = body
    .replace(/\\emph\{([^}]*)\}/g, "<em>$1</em>")
    .replace(/\\ref\{([^}]*)\}/g, (_, key) => `<a href="#${key}">${labels[key] ?? "?"}</a>`)
    .replace(/~/g, "&nbsp;");

  const html = body
    .split(/\n\s*\n/)
    .map((chunk) => chunk.trim())
    .filter(Boolean)
    .map((chunk) => (chunk.startsWith("<") ? chunk : `<p>${chunk}</p>`))
    .join("\n");

  return { title, html: html.replace(/\u0000(\d+)\u0000/g, (_, i) => math[+i]) };
}

async function renderTexPost() {
  const root = document.getElementById("post");
  const src = await (await fetch(root.dataset.tex)).text();
  const { title, html } = texToHtml(src);
  document.title = title.replace(/\$/g, "");
  root.innerHTML = `<h1>${title.replace(/\$([^$]+)\$/g, "\\($1\\)")}</h1>\n${html}`;
  // load MathJax only after the content exists, so its startup typeset sees it
  const mj = document.createElement("script");
  mj.src = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js";
  document.head.appendChild(mj);
}

renderTexPost();
