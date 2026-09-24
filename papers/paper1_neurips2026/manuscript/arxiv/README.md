# arXiv preprint package

This directory is the public, non-anonymous arXiv export of the first paper.
It combines the main text, appendices, and references in one PDF.

Build from this directory with:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The author line currently lists Bill Chen (University of California, Santa
Cruz and Meta) and Jeremy Andrew Balch (Health Outcomes and Biomedical
Informatics, University of Florida). Confirm the complete author list and
any remaining affiliations before submitting to arXiv.

The source repository is [BariatricRSD](https://github.com/billchenxi/BariatricRSD),
and released checkpoints are hosted at
[Hugging Face](https://huggingface.co/billchenxi/surgical-workflow-models).
