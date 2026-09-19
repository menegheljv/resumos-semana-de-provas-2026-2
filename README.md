# Semana de Provas 2026/2

Site de estudo da turma para as avaliações do período **2026/2 — P4N** (UVV, Publicidade e Propaganda).

**[Abrir o site →](https://menegheljv.github.io/resumos-semana-de-provas-2026-2/)**

## O que tem

| Matéria | Resumo | Revisão relâmpago | Quiz |
|---|---|---|---|
| Marketing | [resumo](materias/marketing/resumo.md) | [cartões](materias/marketing/apresentacao.md) | [20 questões](materias/marketing/quiz.md) |
| Marketing Digital | [resumo](materias/marketing-digital/resumo.md) | [cartões](materias/marketing-digital/apresentacao.md) | [20 questões](materias/marketing-digital/quiz.md) |
| Planejamento e Estratégias de Comunicação Integrada | [resumo](materias/planejamento-comunicacao-integrada/resumo.md) | [cartões](materias/planejamento-comunicacao-integrada/apresentacao.md) | [20 questões](materias/planejamento-comunicacao-integrada/quiz.md) |

Além disso, a **Biblioteca da turma**: uma pasta do Google Drive onde cada aluno sobe seus próprios resumos. O botão está na página inicial do site.

## Formato dos arquivos

- `resumo.md`: `# Título`, um parágrafo de abertura e seções `## 1. Nome`. Destaques com citação iniciada por `**Cai na prova:**`, `**Atenção:**` ou `**Regra de ouro:**`. Mantenha `## Antes de entrar na prova` e `## Fontes` no fim.
- `apresentacao.md`: cada cartão é `## Slide N — Título` seguido de marcadores `-`.
- `quiz.md`: grupos com `## Nome`; cada questão é `### N. Enunciado`, quatro alternativas `A.` a `D.` e a linha `**Resposta: X.** Explicação.`

## Como o site é gerado

Os textos ficam em `materias/<matéria>/` (`resumo.md`, `apresentacao.md`, `quiz.md`). O script `scripts/build.py` transforma esses arquivos nas páginas de `docs/`. O GitHub Actions roda o script a cada push na `master` e publica o resultado no GitHub Pages. Ou seja: **editar um `.md` já atualiza o site.**

Para rodar localmente (só precisa de Python 3, sem instalar nada):

```bash
python3 scripts/build.py
python3 -m http.server 8000 --directory docs
```

Os IDs das pastas do Drive ficam em `site.config.json`.

> Conteúdo baseado nos slides e PDFs das disciplinas. Confira sempre com o material do professor.
