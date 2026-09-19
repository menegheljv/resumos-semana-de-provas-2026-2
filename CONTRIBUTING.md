# Como contribuir

## Quer compartilhar o seu resumo?

Suba o arquivo na **Biblioteca da turma** (pasta do Google Drive, link na página inicial do site). Use a subpasta da matéria e nomeie como `Tema - Seu nome`.

## Achou um erro no site?

Cada resumo tem, no fim da página, o link **Achou um erro? Edite este resumo no GitHub**. Edite o texto, envie a alteração e o site atualiza sozinho depois da revisão. Se preferir, abra uma [issue](../../issues/new/choose).

## Formato dos arquivos (`materias/<matéria>/`)

**`resumo.md`**: um `# Título`, um parágrafo de abertura, e seções `## 1. Nome`. Tabelas, listas e `### subtítulos` funcionam. Para destaques, use citação começando por um rótulo:

```
> **Cai na prova:** texto.
> **Atenção:** texto.
> **Regra de ouro:** texto.
```

Mantenha `## Antes de entrar na prova` (lista de checklist) e `## Fontes` no fim.

**`apresentacao.md`** (revisão relâmpago): cada cartão é `## Slide N — Título` seguido de marcadores `-`.

**`quiz.md`**: grupos com `## Nome do grupo`; cada questão é:

```
### 7. Enunciado da pergunta?

A. Alternativa
B. Alternativa
C. Alternativa
D. Alternativa

**Resposta: C.** Explicação curta do porquê.
```

São sempre 4 alternativas (A a D). Se faltar uma, o build avisa qual questão está errada.

## Regras de conteúdo

- Escreva com suas palavras e cite a aula, o slide ou o livro.
- Prefira frases diretas e revisáveis.
- Não publique dados pessoais, provas de outras turmas ou material que não possa ser compartilhado.
