# Supplement C build

Build locally from repo root:

```bash
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error supplement-c/main.tex
cp supplement-c/main.pdf supplement-c.pdf
```
