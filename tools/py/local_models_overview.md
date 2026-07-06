# Overview of local models

## GPU

```bash
kirill@aw16x-lin:~$ nvidia-smi
Mon Jul  6 11:12:17 2026
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.159.03             Driver Version: 580.159.03     CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 5070 ...    Off |   00000000:02:00.0 Off |                  N/A |
| N/A   53C    P2              9W /   85W |      13MiB /   8151MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A            4449      G   /usr/bin/gnome-shell                      2MiB |
+-----------------------------------------------------------------------------------------+

```

## Ollama models

```bash
kirill@aw16x-lin:~$ ollama ls | sort
NAME                               ID              SIZE      MODIFIED
codegemma:7b-code                  aee9a63c13b9    5.0 GB    7 months ago
deepseek-r1:1.5b                   e0979632db5a    1.1 GB    8 months ago
deepseek-r1:7b                     755ced02ce7b    4.7 GB    6 months ago
deepseek-r1:8b                     6995872bfe4c    5.2 GB    3 days ago
falcon3:7b                         472ea1c89f64    4.6 GB    2 weeks ago
gemma2:9b-instruct-q5_K_M          272e1f3a41a6    6.6 GB    3 weeks ago
gemma4:12b-it-qat                  38044be4f923    7.2 GB    3 weeks ago
gemma4:e2b                         7fbdbf8f5e45    7.2 GB    2 months ago
gemma4:e2b-ctx16k                  a187ea534fc0    7.2 GB    8 days ago
gemma4:e2b-ctx32k                  508b7f75c070    7.2 GB    4 days ago
gemma4:e2b-it-qat                  07ea59a47401    4.3 GB    3 weeks ago
gemma4:e4b-it-qat                  ee6656371218    6.1 GB    3 weeks ago
granite3.1-dense:8b                34d3be74ec54    5.0 GB    3 days ago
llama3.1:8b                        46e0c10c039e    4.9 GB    7 months ago
llama3.1:8b-instruct-q6_K          81e7664fda9c    6.6 GB    3 weeks ago
llama3.1:8b-text-q4_K_M            6f98b5a6e4b7    4.9 GB    3 weeks ago
llama3.2:3b-instruct-q8_0          e410b836fe61    3.4 GB    3 weeks ago
mistral:7b-instruct-v0.3-q4_K_M    6577803aa9a0    4.4 GB    3 weeks ago
nemotron-3-nano:4b-q8_0            c534497d032c    4.2 GB    3 days ago
nemotron-mini:4b-instruct-q8_0     fe86a4d04f9f    4.5 GB    3 days ago
nomic-embed-text:latest            0a109f422b47    274 MB    2 weeks ago
phi4-mini:3.8b-q8_0                0be8e6979181    4.1 GB    2 weeks ago
qwen2.5-coder:3b                   f72c60cabf62    1.9 GB    3 days ago
qwen2.5-coder:7b                   dae161e27b0e    4.7 GB    7 months ago
qwen2.5:3b-instruct-q8_0           cd6aa8b25d7a    3.3 GB    3 weeks ago
qwen2.5:7b                         845dbda0ea48    4.7 GB    2 days ago
qwen3-embedding:0.6b               ac6da0dfba84    639 MB    2 weeks ago
qwen3.5:4b-q4_K_M                  2a654d98e6fb    3.4 GB    2 days ago
qwen3.5:4b-q8_0                    8722f47c2791    5.3 GB    2 weeks ago
qwen3.5:9b-q4_K_M                  6488c96fa5fa    6.6 GB    3 days ago
```

> Models for embeddings are skipped
> `gemma4:e2b-ctx*k` - same model as `gemma4:e2b` but different context, is needed for Pydantic AI because passing ctx_num doesn't work

## Ollama models that won't fit into GPU

Check [result_analysis.ipynb](./tailor_cv_eval/tools/eval_performance/result_analysis.ipynb) and [eval_performance](./tailor_cv_eval/tools/eval_performance) for more information

|     | Model                           | GPU Usage | GPU Info           | Options                         | Run Name                   |
| --- | ------------------------------- | --------- | ------------------ | ------------------------------- | -------------------------- |
| 0   | llama3.1:8b-instruct-q6_K       | 0.530     | 6.19 GB / 11.67 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 1   | gemma2:9b-instruct-q5_K_M       | 0.595     | 5.27 GB / 8.84 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 2   | granite3.1-dense:8b             | 0.603     | 6.11 GB / 10.14 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 3   | codegemma:7b-code               | 0.637     | 6.22 GB / 9.76 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 4   | deepseek-r1:8b                  | 0.640     | 6.18 GB / 9.65 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 5   | gemma4:12b-it-qat               | 0.697     | 5.57 GB / 7.99 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 6   | llama3.1:8b-text-q4_K_M         | 0.712     | 6.31 GB / 8.87 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 7   | llama3.1:8b                     | 0.712     | 6.31 GB / 8.87 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 8   | phi4-mini:3.8b-q8_0             | 0.717     | 6.23 GB / 8.68 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 9   | qwen3.5:9b-q4_K_M               | 0.734     | 5.03 GB / 6.86 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 10  | mistral:7b-instruct-v0.3-q4_K_M | 0.739     | 6.19 GB / 8.38 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 11  | llama3.2:3b-instruct-q8_0       | 0.748     | 6.24 GB / 8.35 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 12  | falcon3:7b                      | 0.773     | 6.20 GB / 8.02 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 13  | qwen3.5:4b-q8_0                 | 0.840     | 5.33 GB / 6.34 GB  | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |

## Ollama models that use 100% GPU

| Model | GPU Usage                      | GPU Info | Options           | Run Name                        |
| ----- | ------------------------------ | -------- | ----------------- | ------------------------------- | -------------------------- |
| 0     | gemma4:e2b                     | 1.0      | 1.52 GB / 1.52 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 1     | gemma4:e2b-ctx16k              | 1.0      | 1.52 GB / 1.52 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 2     | gemma4:e2b-ctx32k              | 1.0      | 1.52 GB / 1.52 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 3     | gemma4:e2b-it-qat              | 1.0      | 1.62 GB / 1.62 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 4     | deepseek-r1:1.5b               | 1.0      | 1.97 GB / 1.97 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 5     | gemma4:e4b-it-qat              | 1.0      | 2.80 GB / 2.80 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 6     | qwen2.5-coder:3b               | 1.0      | 3.13 GB / 3.13 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 7     | qwen3.5:4b-q4_K_M              | 1.0      | 3.76 GB / 3.76 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 8     | nemotron-mini:4b-instruct-q8_0 | 1.0      | 3.91 GB / 3.91 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 9     | nemotron-3-nano:4b-q8_0        | 1.0      | 4.38 GB / 4.38 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 10    | qwen2.5:3b-instruct-q8_0       | 1.0      | 4.39 GB / 4.39 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 11    | deepseek-r1:7b                 | 1.0      | 5.98 GB / 5.98 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 12    | qwen2.5-coder:7b               | 1.0      | 5.98 GB / 5.98 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
| 13    | qwen2.5:7b                     | 1.0      | 5.98 GB / 5.98 GB | ctx: 32768, pred: -1, temp: 0.1 | m30_ctx32k_temp01_predneg1 |
