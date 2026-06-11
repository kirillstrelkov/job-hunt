use clap::Parser;
use prep_for_cv_tail::{render_template, DEFAULT_TEMPLATE};
use std::fs;

#[derive(Parser)]
#[command(name = "prep_for_tail", about = "Combine CV, prompt, and job description into a single markdown file")]
struct Args {
    #[arg(long, help = "Master CV markdown file")]
    cv: String,
    #[arg(long, help = "Prompt for LLM text file")]
    prompt: String,
    #[arg(long, help = "Job description text file")]
    jd: String,
    #[arg(short, long, help = "Output markdown file")]
    output: String,
}

fn main() -> anyhow::Result<()> {
    let args = Args::parse();

    let prompt = fs::read_to_string(&args.prompt)
        .map_err(|e| anyhow::anyhow!("Failed to read prompt '{}': {e}", args.prompt))?;
    let cv = fs::read_to_string(&args.cv)
        .map_err(|e| anyhow::anyhow!("Failed to read CV '{}': {e}", args.cv))?;
    let jd = fs::read_to_string(&args.jd)
        .map_err(|e| anyhow::anyhow!("Failed to read job description '{}': {e}", args.jd))?;

    let result = render_template(DEFAULT_TEMPLATE, prompt.trim(), cv.trim(), jd.trim());

    fs::write(&args.output, &result)
        .map_err(|e| anyhow::anyhow!("Failed to write output '{}': {e}", args.output))?;

    println!("Output written to {}", args.output);
    Ok(())
}
