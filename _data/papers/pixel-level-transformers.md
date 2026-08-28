---
title: "Pixel-Level Transformers in Remote Sensing: A Canopy Height Case Study"
date: 2026-11-03
subtitle: SIGSPATIAL '26
modalLabel: SIGSPATIAL · Nov 2026
links:
  - label: Paper
    url: https://doi.org/10.1145/3841645.3842978
  - label: Code
    icon: github
    url: https://github.com/SvenLigensa/pixel-level-transformers
# First row of the "Further Information" table.
authors: [Sven Ligensa, Jan Pauls, Karsten Schrödter, Ibrahim Fayad, Fabian Gieseke]
---

This paper builds on top of my master's thesis, addressing the same task of pixel-wise regression to predict canopy height based on satellite imagery.
Our first series of experiments comprehensively studies the effects of two impactful hyperparameters of Vision Transformers: patch size and model dimension.
A second series of experiments shows that using efficient attention results in a favorable trade-off between efficiency and performance, beating shifted window attention and even flash attention, an optimized and exact implementation of vanilla attention.
We further find that higher-quality labels (obtained via Airborne Laser Scanning) serve as a better ground truth for evaluating model predictions than the noisy and sparse labels the models are trained on.
