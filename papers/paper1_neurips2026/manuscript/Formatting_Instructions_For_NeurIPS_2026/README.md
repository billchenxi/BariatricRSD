# Final Draft

Clean standalone draft package for the NeurIPS 2026 submission.

Build commands:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main_short.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error main_supplementary.tex
```

Contents:

- `main_short.tex`: main submission wrapper.
- `body_main_short.tex`: final main-body text.
- `main_supplementary.tex` and `body_appendix.tex`: supplementary material.
- `figures/`: only figures referenced by the main or supplementary TeX files.
- `figure_scripts/`: scripts for the new main Figure 1 and Figure 2 assets.
