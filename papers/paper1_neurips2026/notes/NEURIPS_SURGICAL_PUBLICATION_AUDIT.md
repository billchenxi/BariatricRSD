# NeurIPS biomedical-surgery publication audit

Audit date: 2026-07-29

## Scope and method

Source: official NeurIPS proceedings indexes for 2021–2025.

1. Record the total number of papers reported by each annual index.
2. Search paper titles for the literal strings `surgery` or `surgical`
   (case-insensitive).
3. Manually exclude nonmedical uses, such as “gradient surgery” and
   “semantic surgery.”
4. Classify the remaining biomedical-surgery titles by proceedings year
   and track.

This is deliberately a conservative title-based audit. It does not count
adjacent biomedical papers whose titles omit both search terms (for
example, some endoscopy papers), and it is not a full bibliometric
systematic review.

## Results

| Year | All proceedings papers | Biomedical-surgery title matches |
|---:|---:|---:|
| 2021 | 2,334 | 0 |
| 2022 | 2,834 | 1 |
| 2023 | 3,540 | 2 |
| 2024 | 4,493 | 2 |
| 2025 | 5,823 | 3 |
| **Total** | **19,024** | **8 (0.042%)** |

Five of the eight papers were published in the Datasets & Benchmarks
track. None addressed remaining-surgery-duration prediction.

## Included papers

| Year | Track | Title |
|---:|---|---|
| 2022 | Datasets & Benchmarks | OpenSRH: optimizing brain tumor surgery using intraoperative stimulated Raman histology |
| 2023 | Datasets & Benchmarks | SARAMIS: Simulation Assets for Robotic Assisted and Minimally Invasive Surgery |
| 2023 | Main | Text Promptable Surgical Instrument Segmentation with Vision-Language Models |
| 2024 | Datasets & Benchmarks | SurgicAI: A Hierarchical Platform for Fine-Grained Surgical Policy Learning and Benchmarking |
| 2024 | Main | Procedure-Aware Surgical Video-language Pretraining with Hierarchical Knowledge Augmentation |
| 2025 | Datasets & Benchmarks | SonoGym: High Performance Simulation for Challenging Surgical Tasks with Robotic Ultrasound |
| 2025 | Datasets & Benchmarks | EgoExOR: An Ego-Exo-Centric Operating Room Dataset for Surgical Activity Understanding |
| 2025 | Main | Towards Dynamic 3D Reconstruction of Hand-Instrument Interaction in Ophthalmic Surgery |

## Interpretation

The statistic supports a limited statement: biomedical surgery is
sparsely represented in recent NeurIPS proceedings, particularly as a
datasets-and-evaluation topic. It does not establish bias in reviewing,
nor does it show that all biomedical AI is underrepresented.

Several of the five Datasets & Benchmarks precedents use simulation or
emulated procedures, consistent with the difficulty of collecting and
releasing governed patient data. EgoExOR, for example, contains 94
minutes from two emulated procedures. These precedents support evaluating
domain-specific resources by scientific and annotation value rather than
by raw scale alone.

