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

## Source archive rule

Source archives are built from the active theorem-note and manual tree. Manual provenance is manual-local: source section, raw setup when present, script when present, derived CSV when present, figure artifact when present, and audit file when present.
