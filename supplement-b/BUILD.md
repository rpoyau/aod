# Supplement B build

Build locally from repo root:

```bash
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error supplement-b/main.tex
cp supplement-b/main.pdf supplement-b.pdf
```
