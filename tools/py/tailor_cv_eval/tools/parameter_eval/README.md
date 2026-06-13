# Parameter Evaluation Tool

This tool helps tune, test, and optimize local Ollama generation hyperparameters (such as `temperature`, `top_p`, `repeat_penalty`, etc.) using a side-by-side benchmarking harness.

## How It Works

1. **Centralized Model Generation**: Promptfoo routes the test queries to our centralized `tools/py/helpers/ollama_helper.py` script. The helper behaves as a custom Python provider for Promptfoo, loading your environment configuration and communicating with your local Ollama instance.
2. **Hyperparameter Scenarios**: The evaluation matrix defines multiple parameter combinations:
   - **Scenario 1 (Baseline)**: `temperature: 0.0`
   - **Scenario 2**: `temperature: 0.5`
   - **Scenario 3**: `temperature: 1.0`
   - **Scenario 4**: `temperature: 0.7`, `top_p: 0.9`
   - **Scenario 5**: `temperature: 0.2`, `repeat_penalty: 1.2`
3. **Assertion Matrix**: The output is evaluated against your job ground truth (`inputs/job1/gt.md`) on:
   - **Semantic Similarity** (using your evaluator model's embeddings).
   - **Factual LLM Rubric** (using your evaluator model as a judge).
   - **ROUGE Overlap** (lexical structure).

## Configuration

This tool respects your `config.yaml` configuration at the root:
- `eval_model`: The local Ollama model to perform evaluations (defaults to `llama3.1:8b`).
- `tmp_output_dir`: The directory where temp files and outputs are saved.
- `llm_prompt_output_file`: The name of the baseline prompt file used as the prompt input.

## How to Use

Follow these steps to run the parameter evaluations:

### Step 1: Pre-generate a Target Prompt
The parameter tuning runs your configured prompt against multiple parameters. Ensure a prompt exists in the outputs folder:
```bash
just generate-prompt-for-jd
```

### Step 2: Run Parameter Tuning
Execute the tuning sweep:
```bash
just eval-params
```
Promptfoo will invoke `tools/py/helpers/ollama_helper.py` 5 times (once for each parameter variant) and then execute assertions to grade the outputs.

### Step 3: View Results
Once execution is complete, launch the interactive dashboard to compare details of each parameter set:
```bash
npx promptfoo view
```
Look for which parameter combination delivers the highest semantic similarity and satisfies the LLM correctness rubric best.
