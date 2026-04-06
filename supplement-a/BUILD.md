# Supplement A build

Build locally from repo root:

```bash
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error supplement-a/main.tex
cp supplement-a/main.pdf supplement-a.pdf
```
