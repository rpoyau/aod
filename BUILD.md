# Build notes

## Public build targets

- `main.tex`
- `manual/main.tex`

## Example local build

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error manual/main.tex
cp manual/main.pdf manual.pdf
```

## Public release assets

- `main.pdf`
- `manual.pdf`
- optional source zip
- optional `audit-pack.zip`

## Archived source fragments

- `archive/supplement-a/`
- `archive/supplement-b/`
- `archive/supplement-c/`
