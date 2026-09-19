#!/usr/bin/env python3
"""Gera o site (pasta docs/) a partir dos arquivos .md de materias/.

Uso:  python3 scripts/build.py

Só usa a biblioteca padrão. O GitHub Actions roda este script antes de publicar,
então basta editar um .md (resumo, apresentação ou quiz) para o site atualizar.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MAT = ROOT / "materias"
CFG = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))

SUBJECTS = [
    {
        "slug": "marketing",
        "page": "marketing.html",
        "quiz_page": "quiz-marketing.html",
        "num": "01",
        "color": "violet",
        "name": "Marketing",
        "title_html": "Marketing<span class=\"dot\">.</span>",
        "tagline": "Valor percebido, comportamento, jornada, marketing social e segmentação B2C e B2B.",
        "prof": "Prof. Neil Palacios Jr.",
    },
    {
        "slug": "marketing-digital",
        "page": "marketing-digital.html",
        "quiz_page": "quiz-marketing-digital.html",
        "num": "02",
        "color": "blue",
        "name": "Marketing Digital",
        "title_html": "Marketing<br><em>Digital.</em>",
        "tagline": "Inbound, SEO, mídia programática, performance, anúncios por rede e gestão de crises.",
        "prof": "",
    },
    {
        "slug": "planejamento-comunicacao-integrada",
        "page": "planejamento-comunicacao-integrada.html",
        "quiz_page": "quiz-planejamento.html",
        "num": "03",
        "color": "teal",
        "name": "Planejamento e Estratégias de Comunicação Integrada",
        "short": "Planejamento",
        "title_html": "Planejamento<br><em>integrado.</em>",
        "tagline": "Comunicação organizacional integrada, marca, identidade, imagem e reputação.",
        "prof": "",
    },
]


# ---------------------------------------------------------------- markdown mínimo

def esc(text):
    return html.escape(text, quote=False)


def inline(text):
    t = esc(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noreferrer">\1</a>', t)
    return t


def slugify(text):
    text = re.sub(r"^\d+\.\s*", "", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    text = (text.replace("ç", "c").replace("ã", "a").replace("õ", "o")
            .replace("á", "a").replace("à", "a").replace("â", "a")
            .replace("é", "e").replace("ê", "e").replace("í", "i")
            .replace("ó", "o").replace("ô", "o").replace("ú", "u"))
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


CALLOUTS = [
    ("cai na prova", "exam", "Cai na prova"),
    ("atenção", "warn", "Atenção"),
    ("regra de ouro", "tip", "Regra de ouro"),
    ("definição", "def", "Definição"),
]


def parse_blocks(lines):
    """Converte linhas markdown em uma lista de blocos simples."""
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            blocks.append(("h", len(m.group(1)), m.group(2).strip()))
            i += 1
            continue
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(lines[i].strip().strip("|").split("|"))
                i += 1
            head, body = rows[0], rows[2:]
            blocks.append(("table", [c.strip() for c in head], [[c.strip() for c in r] for r in body]))
            continue
        if re.match(r"^\s*-\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*-\s+", lines[i]):
                items.append(re.sub(r"^\s*-\s+", "", lines[i]).strip())
                i += 1
            blocks.append(("ul", items))
            continue
        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]).strip())
                i += 1
            blocks.append(("ol", items))
            continue
        if line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i][1:].strip())
                i += 1
            blocks.append(("quote", " ".join(quote)))
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|\s*-\s|\s*\d+\.\s|>|\s*\|)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append(("p", " ".join(para)))
    return blocks


def render_block(block):
    kind = block[0]
    if kind == "p":
        return f"<p>{inline(block[1])}</p>"
    if kind in ("ul", "ol"):
        return f"<{kind}>" + "".join(f"<li>{inline(x)}</li>" for x in block[1]) + f"</{kind}>"
    if kind == "table":
        head = "".join(f"<th>{inline(c)}</th>" for c in block[1])
        labels = [html.escape(h) for h in block[1]]
        body = "".join(
            "<tr>" + "".join(
                f'<td data-label="{labels[i] if i < len(labels) else ""}">{inline(c)}</td>' for i, c in enumerate(row)
            ) + "</tr>"
            for row in block[2]
        )
        cls = ' class="tbl-num"' if block[1] and block[1][0].strip() == "#" else ""
        return f'<div class="table-wrap"><table{cls}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    if kind == "quote":
        text = block[1]
        low = text.lower()
        for key, cls, label in CALLOUTS:
            if low.startswith(f"**{key}"):
                return f'<aside class="callout callout-{cls}"><p>{inline(text)}</p></aside>'
        return f"<blockquote><p>{inline(text)}</p></blockquote>"
    return ""


def render_h3(text):
    return f"<h3>{inline(text)}</h3>"


def render_sections(md):
    """Devolve (lead_html, [(titulo, slug, html)]) — uma seção por H2."""
    lines = md.splitlines()
    blocks = parse_blocks(lines)
    lead, sections, current = [], [], None
    for b in blocks:
        if b[0] == "h" and b[1] == 1:
            continue
        if b[0] == "h" and b[1] == 2:
            current = {"title": b[2], "slug": slugify(b[2]), "parts": []}
            sections.append(current)
            continue
        if b[0] == "h" and b[1] == 3:
            piece = render_h3(b[2])
        else:
            piece = render_block(b)
        (current["parts"] if current else lead).append(piece)
    return "".join(lead), [(s["title"], s["slug"], "".join(s["parts"])) for s in sections]


# ---------------------------------------------------------------- quiz

def parse_quiz(md):
    groups, group, q = [], None, None
    for raw in md.splitlines():
        line = raw.rstrip()
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            group = {"title": m.group(1).strip(), "questions": []}
            groups.append(group)
            q = None
            continue
        m = re.match(r"^###\s+(\d+)\.\s+(.*)$", line)
        if m:
            q = {"n": int(m.group(1)), "text": m.group(2).strip(), "options": [], "answer": "", "why": ""}
            if group is None:
                group = {"title": "", "questions": []}
                groups.append(group)
            group["questions"].append(q)
            continue
        if q is None:
            continue
        m = re.match(r"^([A-D])\.\s+(.*)$", line)
        if m:
            q["options"].append((m.group(1), m.group(2).strip()))
            continue
        m = re.match(r"^\*\*Resposta:\s*([A-D])\.\*\*\s*(.*)$", line)
        if m:
            q["answer"], q["why"] = m.group(1), m.group(2).strip()
    total = sum(len(g["questions"]) for g in groups)
    for g in groups:
        for question in g["questions"]:
            if len(question["options"]) != 4 or not question["answer"]:
                raise SystemExit(f"Questão {question['n']} malformada: {question['text'][:60]}")
    return groups, total


def render_quiz(groups, total, slug):
    out = []
    for g in groups:
        if g["title"]:
            out.append(f'<h2 class="quiz-group">{inline(g["title"])}</h2>')
        for q in g["questions"]:
            opts = "".join(
                f'<button type="button" class="option" data-key="{k}"><span class="key">{k}</span><span class="opt-text">{inline(t)}</span></button>'
                for k, t in q["options"]
            )
            out.append(
                f'<article class="question" id="q{q["n"]}" data-answer="{q["answer"]}">'
                f'<p class="q-num">Questão {q["n"]} de {total}</p>'
                f'<h3>{inline(q["text"])}</h3>'
                f'<div class="options">{opts}</div>'
                f'<div class="explain" hidden><p><strong>Gabarito: {q["answer"]}.</strong> {inline(q["why"])}</p></div>'
                f"</article>"
            )
    return "".join(out)


# ---------------------------------------------------------------- apresentação (cartões)

def parse_cards(md):
    lead, cards, cur = [], [], None
    for raw in md.splitlines():
        line = raw.rstrip()
        m = re.match(r"^##\s+Slide\s+(\d+)\s+[—-]\s+(.*)$", line)
        if m:
            cur = {"n": int(m.group(1)), "title": m.group(2).strip(), "items": []}
            cards.append(cur)
            continue
        if line.startswith("# "):
            continue
        if cur is None:
            if line.strip():
                lead.append(line.strip())
            continue
        m = re.match(r"^\s*-\s+(.*)$", line)
        if m:
            cur["items"].append(m.group(1).strip())
    return " ".join(lead), cards


def render_cards(cards):
    out = []
    for c in cards:
        items = "".join(f"<li>{inline(x)}</li>" for x in c["items"])
        out.append(
            f'<article class="flash"><span class="flash-n">{c["n"]:02d}</span>'
            f'<h3>{inline(c["title"])}</h3><ul>{items}</ul></article>'
        )
    return "".join(out)


# ---------------------------------------------------------------- páginas

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
)

SPECIAL = ("antes-de-entrar-na-prova", "fontes")


def strip_num(title):
    return re.sub(r"^\d+\.\s*", "", title)


def drive_folder_url(key="root"):
    return f"https://drive.google.com/drive/folders/{CFG['drive'][key]}"


def drive_embed_url():
    return f"https://drive.google.com/embeddedfolderview?id={CFG['drive']['root']}#grid"


def head(title, desc, body_class=""):
    return (
        "<!doctype html>\n"
        '<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta name="description" content="{esc(desc)}">\n'
        '<meta name="theme-color" content="#0d0b11">\n'
        f"<title>{esc(title)}</title>\n{FONTS}\n"
        '<link rel="stylesheet" href="style.css">\n'
        '<script src="app.js" defer></script>\n'
        f'</head>\n<body class="{body_class}">\n'
        '<a class="skip" href="#conteudo">Pular para o conteúdo</a>\n'
    )


def topbar(links):
    items = "".join(f'<a href="{h}">{esc(t)}</a>' for h, t in links)
    return (
        '<header class="topbar"><div class="wrap topbar-in">'
        '<a class="brand" href="index.html" aria-label="Início">P4N<span>.</span></a>'
        f'<nav class="toplinks" aria-label="Seções">{items}</nav>'
        f'<a class="top-cta" href="{drive_folder_url()}" target="_blank" rel="noreferrer">Enviar resumo</a>'
        "</div></header>\n"
    )


def footer():
    return (
        '<footer class="footer"><div class="wrap">'
        "Semana de Provas 2026/2 · Feito pela turma. Confira sempre com o material do professor."
        "</div></footer>\n</body>\n</html>\n"
    )


def content_sections(d):
    return [x for x in d["sections"] if x[1] not in SPECIAL]


def load(subject):
    base = MAT / subject["slug"]
    resumo = (base / "resumo.md").read_text(encoding="utf-8")
    apresentacao = (base / "apresentacao.md").read_text(encoding="utf-8")
    quiz = (base / "quiz.md").read_text(encoding="utf-8")
    lead, sections = render_sections(resumo)
    _, cards = parse_cards(apresentacao)
    groups, total = parse_quiz(quiz)
    quiz_lead = ""
    for line in quiz.splitlines()[1:]:
        if line.strip():
            quiz_lead = line.strip()
            break
    return {"lead": lead, "sections": sections, "cards": cards, "groups": groups, "total": total, "quiz_lead": quiz_lead}


def library_block():
    return (
        '<section class="library" id="biblioteca"><div class="wrap library-in">'
        '<div class="library-text"><h2>Biblioteca da turma</h2>'
        "<p>Suba seu resumo na pasta do Drive e use os dos colegas. Nomeie como <code>Tema - Seu nome</code>. Precisa de conta Google.</p>"
        f'<a class="button big" href="{drive_folder_url()}" target="_blank" rel="noreferrer">Enviar meu resumo</a></div>'
        '<div class="drive-embed">'
        f'<iframe src="{drive_embed_url()}" title="Pasta do Google Drive com os resumos da turma" loading="lazy"></iframe>'
        f'<p class="embed-note"><a href="{drive_folder_url()}" target="_blank" rel="noreferrer">Abrir no Drive ↗</a></p>'
        "</div></div></section>\n"
    )


def build_index(data):
    cards = "".join(
        f'<article class="subject-card card-{s["color"]}">'
        f'<span class="card-num">{s["num"]}</span>'
        f'<h3><a href="{s["page"]}">{esc(s["name"])}</a></h3>'
        f'<p>{esc(s["tagline"])}</p>'
        f'<div class="card-actions"><a class="button" href="{s["page"]}">Resumo</a>'
        f'<a class="button ghost" href="{s["quiz_page"]}">Quiz</a></div></article>'
        for s in SUBJECTS
    )
    page = (
        head("Semana de Provas 2026/2 · P4N", "Resumos, revisão relâmpago e quizzes das três matérias da semana de provas 2026/2, mais uma biblioteca de resumos da turma.", "page-home")
        + topbar([("#materias", "Matérias"), ("#biblioteca", "Biblioteca")])
        + '<header class="hero hero-home"><div class="wrap hero-in">'
        '<p class="eyebrow">UVV · P4N · 2026/2</p>'
        "<h1>Semana de<br><em>provas.</em></h1>"
        '<p class="lede">Resumo, revisão e quiz das três matérias.</p>'
        '<div class="hero-actions"><a class="button big" href="#materias">Começar a revisar</a></div>'
        "</div></header>\n"
        '<main id="conteudo">'
        f'<section class="wrap block" id="materias"><div class="subjects">{cards}</div></section>'
        + library_block()
        + "</main>\n"
        + footer()
    )
    (DOCS / "index.html").write_text(page, encoding="utf-8")


def build_subject(s, d):
    color = s["color"]
    toc = "".join(
        f'<li><a href="#{slug}">{esc(strip_num(title))}</a></li>'
        for title, slug, _ in d["sections"] if slug != "fontes"
    )
    body = []
    for title, slug, content in d["sections"]:
        if slug == "fontes":
            body.append(f'<section class="sec sec-sources" id="{slug}"><h2>Fontes</h2>{content}</section>')
        elif slug == "antes-de-entrar-na-prova":
            body.append(f'<section class="sec sec-check" id="{slug}"><h2>Antes de entrar na prova</h2>{content}</section>')
        else:
            body.append(f'<section class="sec" id="{slug}"><h2>{inline(title)}</h2>{content}</section>')
    page = (
        head(f"{s['name']} · Semana de Provas", s["tagline"], f"page-light accent-{color}")
        + topbar([("#resumo", "Resumo"), ("#revisao", "Revisão"), (s["quiz_page"], "Quiz")])
        + '<header class="hero hero-sub"><div class="wrap hero-in">'
        f'<p class="eyebrow">Matéria {s["num"]}</p><h1>{s["title_html"]}</h1>'
        f'<p class="lede">{esc(s["tagline"])}</p>'
        '<div class="hero-actions"><a class="button big" href="#resumo">Ler o resumo</a>'
        f'<a class="button big ghost" href="{s["quiz_page"]}">Fazer o quiz</a></div>'
        "</div></header>\n"
        '<main id="conteudo">'
        '<div class="wrap subject-layout" id="resumo">'
        f'<aside class="toc"><details open><summary>Nesta página</summary><ol>{toc}<li><a href="#revisao">Revisão relâmpago</a></li></ol></details></aside>'
        f'<article class="resumo"><div class="resumo-lead">{d["lead"]}</div>{"".join(body)}</article>'
        "</div>"
        '<section class="wrap block" id="revisao"><h2 class="block-title">Revisão relâmpago</h2>'
        f'<div class="flash-grid">{render_cards(d["cards"])}</div></section>'
        '<section class="band"><div class="wrap band-in"><h2>Agora teste o que aprendeu.</h2>'
        f'<div class="band-actions"><a class="button big" href="{s["quiz_page"]}">Fazer o quiz · {d["total"]} questões</a>'
        f'<a class="button big ghost" href="{drive_folder_url(s["slug"])}" target="_blank" rel="noreferrer">Enviar meu resumo</a></div></div></section>'
        "</main>\n"
        + footer()
    )
    (DOCS / s["page"]).write_text(page, encoding="utf-8")


def build_quiz(s, d):
    color = s["color"]
    short = s.get("short", s["name"])
    page = (
        head(f"Quiz de {short} · Semana de Provas", f"Quiz de {s['name']} com gabarito e explicação na hora.", f"page-light accent-{color}")
        + topbar([(s["page"], "Voltar ao resumo")])
        + '<header class="hero hero-sub"><div class="wrap hero-in">'
        f'<h1>{esc(short)}<br><em>quiz.</em></h1>'
        f'<p class="lede">{inline(d["quiz_lead"])}</p></div></header>\n'
        '<main id="conteudo" class="wrap quiz-wrap">'
        '<div class="quiz-bar" role="status" aria-live="polite"><div class="quiz-stats">'
        f'<span>Respondidas <strong data-answered>0</strong>/<span data-total>{d["total"]}</span></span>'
        '<span>Acertos <strong data-correct>0</strong></span></div>'
        '<button type="button" class="link-btn" data-reset>Refazer</button>'
        '<div class="progress" aria-hidden="true"><i data-progress></i></div></div>'
        f'<div class="quiz" data-quiz="{s["slug"]}" data-total="{d["total"]}">{render_quiz(d["groups"], d["total"], s["slug"])}</div>'
        '<section class="result" data-result hidden>'
        '<h2 data-result-title></h2><p data-result-text></p>'
        '<div class="hero-actions"><button type="button" class="button" data-reset>Refazer o quiz</button>'
        f'<a class="button ghost" href="{s["page"]}#resumo">Voltar ao resumo</a>'
        '<button type="button" class="button ghost" data-first-wrong hidden>Ver primeiro erro</button></div></section>'
        "</main>\n"
        + footer()
    )
    (DOCS / s["quiz_page"]).write_text(page, encoding="utf-8")


def main():
    DOCS.mkdir(exist_ok=True)
    data = {s["slug"]: load(s) for s in SUBJECTS}
    build_index(data)
    for s in SUBJECTS:
        build_subject(s, data[s["slug"]])
        build_quiz(s, data[s["slug"]])
    print("Site gerado em docs/:", ", ".join(sorted(p.name for p in DOCS.glob("*.html"))))


if __name__ == "__main__":
    main()
