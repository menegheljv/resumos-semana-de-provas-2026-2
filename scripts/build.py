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
REPO = CFG["repo"]
BRANCH = CFG["branch"]

SUBJECTS = [
    {
        "slug": "marketing",
        "page": "marketing.html",
        "quiz_page": "quiz-marketing.html",
        "num": "01",
        "color": "pink",
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
        "color": "purple",
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
        "color": "blue",
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
        body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in block[2])
        return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
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
    '<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
)


def head(title, desc, extra_body_class=""):
    return (
        "<!doctype html>\n"
        '<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta name="description" content="{esc(desc)}">\n'
        '<meta name="theme-color" content="#17151a">\n'
        f"<title>{esc(title)}</title>\n{FONTS}\n"
        '<link rel="stylesheet" href="style.css">\n'
        '<script src="app.js" defer></script>\n'
        f'</head>\n<body class="{extra_body_class}">\n'
        '<a class="skip" href="#conteudo">Pular para o conteúdo</a>\n'
    )


def topbar(links):
    items = "".join(f'<a href="{h}">{esc(t)}</a>' for h, t in links)
    return (
        '<header class="topbar"><div class="wrap topbar-in">'
        '<a class="brand" href="index.html" aria-label="Início">P4N<span>.</span></a>'
        f'<nav class="toplinks" aria-label="Seções">{items}</nav>'
        f'<a class="repo-link" href="{REPO}" target="_blank" rel="noreferrer">GitHub ↗</a>'
        "</div></header>\n"
    )


def footer():
    return (
        '<footer class="footer"><div class="wrap footer-in">'
        "<div><strong>Semana de Provas 2026/2</strong>"
        "<p>Feito pela turma, para a turma. Conferido com os slides da disciplina. Na dúvida, vale o que o professor disse em aula.</p></div>"
        '<nav aria-label="Rodapé">'
        '<a href="index.html#biblioteca">Biblioteca da turma</a>'
        f'<a href="{REPO}/issues/new/choose" target="_blank" rel="noreferrer">Achou um erro?</a>'
        f'<a href="{REPO}" target="_blank" rel="noreferrer">Código no GitHub ↗</a>'
        "</nav></div></footer>\n</body>\n</html>\n"
    )


def drive_folder_url(key="root"):
    return f"https://drive.google.com/drive/folders/{CFG['drive'][key]}"


def drive_embed_url():
    return f"https://drive.google.com/embeddedfolderview?id={CFG['drive']['root']}#grid"


SPECIAL = ("antes-de-entrar-na-prova", "fontes")


def strip_num(title):
    return re.sub(r"^\d+\.\s*", "", title)


def content_sections(d):
    return [x for x in d["sections"] if x[1] not in SPECIAL]


def load(subject):
    base = MAT / subject["slug"]
    resumo = (base / "resumo.md").read_text(encoding="utf-8")
    apresentacao = (base / "apresentacao.md").read_text(encoding="utf-8")
    quiz = (base / "quiz.md").read_text(encoding="utf-8")
    lead, sections = render_sections(resumo)
    card_lead, cards = parse_cards(apresentacao)
    groups, total = parse_quiz(quiz)
    quiz_lead = ""
    for line in quiz.splitlines()[1:]:
        if line.strip():
            quiz_lead = line.strip()
            break

    return {
        "lead": lead, "sections": sections, "card_lead": card_lead, "cards": cards,
        "groups": groups, "total": total, "quiz_lead": quiz_lead,
    }


def library_block(compact=False, subject=None):
    if subject:
        folder = drive_folder_url(subject["slug"])
        return (
            '<section class="band band-drive" id="drive"><div class="wrap band-in">'
            '<div><p class="eyebrow">Biblioteca da turma</p>'
            f'<h2>Fez um resumo de {esc(subject.get("short", subject["name"]))}? Suba aqui.</h2>'
            "<p>Resumo, mapa mental, lista de exercícios. Tudo que ajudar a turma a estudar entra na pasta da matéria.</p></div>"
            '<div class="band-actions">'
            f'<a class="button" href="{folder}" target="_blank" rel="noreferrer">Enviar meu resumo ↗</a>'
            '<a class="button ghost" href="index.html#biblioteca">Ver a biblioteca</a></div></div></section>\n'
        )
    tiles = "".join(
        f'<a class="folder-tile tile-{s["color"]}" href="{drive_folder_url(s["slug"])}" target="_blank" rel="noreferrer">'
        f'<span class="folder-n">{s["num"]}</span><span class="folder-name">{esc(s.get("short", s["name"]))}</span>'
        '<span class="folder-go">Abrir pasta ↗</span></a>'
        for s in SUBJECTS
    )
    return (
        '<section class="library" id="biblioteca"><div class="wrap">'
        '<div class="section-head"><p class="eyebrow">Biblioteca da turma</p>'
        "<h2>Estudou? Devolva pra turma.</h2>"
        "<p>Uma pasta do Google Drive compartilhada, com uma subpasta por matéria. Sobe o seu resumo, baixa o dos colegas. Você precisa de uma conta Google.</p></div>"
        '<div class="library-grid"><div class="library-side">'
        f'<a class="button big" href="{drive_folder_url()}" target="_blank" rel="noreferrer">Enviar meu resumo ↗</a>'
        f'<div class="folder-tiles">{tiles}</div>'
        '<h3>Como enviar</h3><ol class="steps">'
        "<li>Abra a pasta da matéria.</li>"
        "<li>Arraste o arquivo (PDF, Docs, imagem) para dentro.</li>"
        "<li>Nomeie assim: <code>Tema - Seu nome</code>.</li></ol>"
        '<h3>Regras rápidas</h3><ul class="rules">'
        "<li>Escreva com suas palavras e cite a aula ou o slide.</li>"
        "<li>Nada de dado pessoal nem prova de outras turmas.</li>"
        "<li>Apague só o que você mesmo enviou.</li></ul></div>"
        '<div class="drive-embed">'
        f'<iframe src="{drive_embed_url()}" title="Pasta do Google Drive com os resumos da turma" loading="lazy"></iframe>'
        f'<p class="embed-note">Se o Google pedir cookies, clique em permitir. Não apareceu? <a href="{drive_folder_url()}" target="_blank" rel="noreferrer">Abra a pasta direto no Drive ↗</a></p>'
        "</div></div></div></section>\n"
    )


def build_index(data):
    total_q = sum(d["total"] for d in data.values())
    total_s = sum(len(content_sections(d)) for d in data.values())
    cards = []
    for s in SUBJECTS:
        d = data[s["slug"]]
        cards.append(
            f'<article class="subject-card card-{s["color"]}">'
            f'<div class="card-top"><span class="card-num">{s["num"]}</span>'
            f'<span class="card-meta">{len(content_sections(d))} blocos · {d["total"]} questões</span></div>'
            f'<h3><a href="{s["page"]}">{esc(s["name"])}</a></h3>'
            f'<p>{esc(s["tagline"])}</p>'
            f'<div class="card-actions"><a class="button" href="{s["page"]}">Ler resumo</a>'
            f'<a class="button ghost" href="{s["quiz_page"]}">Fazer quiz</a></div></article>'
        )
    steps = (
        '<ol class="how">'
        '<li><span>1</span><div><h3>Leia o resumo</h3><p>Cada matéria tem um resumo curto, com o que costuma cair destacado.</p></div></li>'
        '<li><span>2</span><div><h3>Teste-se no quiz</h3><p>Respondeu, viu o gabarito na hora, com explicação. Erre aqui, não na prova.</p></div></li>'
        '<li><span>3</span><div><h3>Complete com a turma</h3><p>Suba seu resumo na biblioteca e use o dos colegas.</p></div></li></ol>'
    )
    page = (
        head("Semana de Provas 2026/2 · P4N", "Resumos, revisão relâmpago e quizzes das três matérias da semana de provas 2026/2, mais uma biblioteca de resumos da turma.")
        + topbar([("#materias", "Matérias"), ("#como", "Como estudar"), ("#biblioteca", "Biblioteca")])
        + '<header class="hero hero-home"><div class="wrap hero-in">'
        '<p class="eyebrow">UVV · P4N · 2026/2</p>'
        "<h1>Semana de<br><em>provas.</em></h1>"
        '<p class="lede">Três matérias, um lugar. Resumo direto, quiz com gabarito na hora e uma pasta para a turma dividir o que estudou.</p>'
        '<div class="hero-actions"><a class="button big" href="#materias">Começar a revisar</a>'
        '<a class="button big ghost" href="#biblioteca">Enviar meu resumo</a></div>'
        f'<ul class="stats"><li><strong>3</strong><span>matérias</span></li><li><strong>{total_s}</strong><span>blocos de resumo</span></li><li><strong>{total_q}</strong><span>questões com gabarito</span></li></ul>'
        "</div></header>\n"
        '<main id="conteudo">'
        '<section class="wrap block" id="materias"><div class="section-head"><p class="eyebrow">Matérias</p>'
        "<h2>Escolha uma e comece.</h2></div>"
        f'<div class="subjects">{"".join(cards)}</div></section>'
        f'<section class="wrap block" id="como"><div class="section-head"><p class="eyebrow">Como estudar</p><h2>Três passos, sem enrolação.</h2></div>{steps}</section>'
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
    edit = f"{REPO}/edit/{BRANCH}/materias/{s['slug']}/resumo.md"
    page = (
        head(f"{s['name']} · Semana de Provas", s["tagline"])
        + topbar([("#resumo", "Resumo"), ("#revisao", "Revisão relâmpago"), ("#quiz", "Quiz"), ("#drive", "Biblioteca")])
        + f'<header class="hero hero-sub hero-{color}"><div class="wrap hero-in">'
        f'<p class="eyebrow">Matéria {s["num"]} · 2026/2</p><h1>{s["title_html"]}</h1>'
        f'<p class="lede">{esc(s["tagline"])}</p>'
        f'<div class="hero-actions"><a class="button big" href="#resumo">Ler o resumo</a>'
        f'<a class="button big ghost" href="{s["quiz_page"]}">Fazer o quiz · {d["total"]} questões</a></div>'
        "</div></header>\n"
        '<main id="conteudo">'
        f'<div class="wrap subject-layout accent-{color}" id="resumo">'
        f'<aside class="toc"><details open><summary>Nesta página</summary><ol>{toc}<li><a href="#revisao">Revisão relâmpago</a></li></ol></details></aside>'
        f'<article class="resumo"><div class="resumo-lead">{d["lead"]}</div>{"".join(body)}'
        f'<p class="edit-link"><a href="{edit}" target="_blank" rel="noreferrer">Achou um erro? Edite este resumo no GitHub ↗</a></p></article>'
        "</div>"
        f'<section class="wrap block accent-{color}" id="revisao"><div class="section-head"><p class="eyebrow">Revisão relâmpago</p>'
        f'<h2>Um minuto por cartão.</h2><p>{esc(d["card_lead"])}</p></div>'
        f'<div class="flash-grid">{render_cards(d["cards"])}</div></section>'
        f'<section class="band band-quiz accent-{color}" id="quiz"><div class="wrap band-in"><div>'
        '<p class="eyebrow">Quiz</p>'
        f'<h2>{d["total"]} questões. Gabarito na hora.</h2>'
        "<p>Responda sem consultar o resumo. Cada resposta abre a explicação.</p></div>"
        f'<div class="band-actions"><a class="button big" href="{s["quiz_page"]}">Começar o quiz →</a></div></div></section>\n'
        + library_block(subject=s)
        + "</main>\n"
        + footer()
    )
    (DOCS / s["page"]).write_text(page, encoding="utf-8")


def build_quiz(s, d):
    color = s["color"]
    page = (
        head(f"Quiz de {s.get('short', s['name'])} · Semana de Provas", f"Quiz de {s['name']} com gabarito e explicação na hora.")
        + topbar([("#topo", "Quiz"), (s["page"], "Voltar ao resumo")])
        + f'<header class="hero hero-sub hero-{color}" id="topo"><div class="wrap hero-in">'
        f'<p class="eyebrow">Quiz · {esc(s.get("short", s["name"]))}</p>'
        f'<h1>{esc(s.get("short", s["name"]))}<br><em>quiz.</em></h1>'
        f'<p class="lede">{inline(d["quiz_lead"])}</p></div></header>\n'
        f'<main id="conteudo" class="wrap quiz-wrap accent-{color}">'
        f'<div class="quiz-bar" role="status" aria-live="polite"><div class="quiz-stats">'
        f'<span>Respondidas <strong data-answered>0</strong>/<span data-total>{d["total"]}</span></span>'
        '<span>Acertos <strong data-correct>0</strong></span></div>'
        '<div class="progress" aria-hidden="true"><i data-progress></i></div>'
        '<button type="button" class="link-btn" data-reset>Refazer</button></div>'
        f'<div class="quiz" data-quiz="{s["slug"]}" data-total="{d["total"]}">{render_quiz(d["groups"], d["total"], s["slug"])}</div>'
        '<section class="result" data-result hidden>'
        '<p class="eyebrow">Resultado</p><h2 data-result-title></h2><p data-result-text></p>'
        f'<div class="hero-actions"><button type="button" class="button" data-reset>Refazer o quiz</button>'
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
