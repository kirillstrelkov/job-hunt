# Prompt Evaluation Tool

This tool helps compare and benchmark different LLM prompts side-by-side using Promptfoo.

## How It Works

1. **Baseline Generation**: The tool expects a baseline prompt to already exist at `tmp/outputs/job1/llm_prompt.md` (or the filename set by `llm_prompt_output_file` under `tmp_output_dir` in your `config.yaml`). This baseline prompt represents your starting point.
2. **Setup Evaluation Directory**: The tool copies the baseline prompt to `tmp/outputs/prompt_eval/baseline_prompt.md`.
3. **Candidate Prompts**: You can place any candidate/experimental prompts as `.md` files directly in `tmp/outputs/prompt_eval/` (e.g., `tmp/outputs/prompt_eval/new_prompt.md`).
4. **Promptfoo Evaluation**: Promptfoo executes all `.md` prompts found in `tmp/outputs/prompt_eval/` side-by-side against the ground truth (`inputs/job1/gt.md`). It uses the evaluator model (defined by `eval_model` in your `config.yaml`) to rate and assert the quality.

## Configuration

This tool respects your `config.yaml` configuration at the root:

- `eval_model`: The local Ollama model to use as an evaluator judge (e.g., `llama3.1:8b`).
- `tmp_output_dir`: The root directory for temporary artifacts (defaults to `tmp/outputs`).
- `llm_prompt_output_file`: The filename of the baseline prompt (defaults to `llm_prompt.md`).

---

## How to Use

Follow these steps to evaluate prompt template modifications:

### Step 1: Generate a Baseline

Ensure you have generated the baseline prompt from the project root:

```bash
just generate-prompt-for-jd
```

This saves the baseline prompt to `tmp/outputs/job1/llm_prompt.md`.

### Step 2: Run the Prompt Evaluation

Execute the evaluation command:

```bash
just eval-prompts
```

### Step 3: Add Candidate Prompts

When the script runs, it will copy the baseline and prompt you if only the baseline is found:

```text
[INFO] Only the baseline prompt was found in tmp/outputs/prompt_eval.
Please copy or create your new candidate prompt *.md files in: tmp/outputs/prompt_eval
Press ENTER once you have added your candidate prompt(s) to continue evaluation...
```

Place your modified prompt files into `tmp/outputs/prompt_eval/` and press **ENTER**.

### Step 4: View Results

Once execution is complete, you can review the console grid output or launch the interactive dashboard to view detailed scores, diffs, and generated text:

```bash
just view-promptfoo
```
