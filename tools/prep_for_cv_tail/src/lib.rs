pub const DEFAULT_TEMPLATE: &str = "{prompt}
<cv>
{cv}
</cv>
<job_description>
{jd}
</job_description>";

pub fn render_template(template: &str, prompt: &str, cv: &str, jd: &str) -> String {
    template
        .replace("{prompt}", prompt)
        .replace("{cv}", cv)
        .replace("{jd}", jd)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn render_fills_all_placeholders() {
        let out = render_template(DEFAULT_TEMPLATE, "p", "c", "j");
        assert!(out.contains("p\n"));
        assert!(out.contains("<cv>"));
        assert!(out.contains("c"));
        assert!(out.contains("job_description"));
        assert!(out.contains("j"));
    }

    #[test]
    fn render_custom_template() {
        let t = "P={prompt} C={cv} J={jd}";
        assert_eq!(render_template(t, "pp", "cc", "jj"), "P=pp C=cc J=jj");
    }
}
