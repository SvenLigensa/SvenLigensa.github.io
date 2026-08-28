---
title: Combining Deep Feature Extraction with Locality-Sensitive Hashing for Reverse Image Search
date: 2022-12-22
subtitle: Bachelor Thesis
modalLabel: Bachelor Thesis · University of Münster · Dec 2022
links:
  - label: PDF
    url: https://uni-muenster.sciebo.de/s/x6Ef2N5s6dVNveM
  - label: Code
    icon: github
    url: https://github.com/SvenLigensa/RIS-with-DINO-and-LSH
facts:
  Principal Supervisor: Prof. Fabian Gieseke
  Supervisor: Christian Lülf
  Grade: "1.0"
---

This work presents a system to perform fast reverse image search on hundreds thousands of input images.
First, a Vision Transformer is trained with the self-DIstillation with NO labels (DINO) framework to produce vector embeddings.
Then, Locality-Sensitive Hashing (LSH) is used to perform an approximate nearest neighbors search on the embeddings.
