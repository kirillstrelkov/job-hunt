#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use base64::Engine;

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            render_markdown,
            convert_to_pdf,
            save_pdf,
            pick_save_path,
            load_markdown_file,
            save_text,
            load_yaml_config,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// Render markdown to HTML using comrak (used for Preview tabs).
#[tauri::command]
fn render_markdown(markdown: String) -> String {
    let mut opts = comrak::Options::default();
    opts.extension.tasklist = true;
    comrak::markdown_to_html(&markdown, &opts)
}

/// Convert markdown to PDF, store result in a temp file, return base64-encoded PDF.
#[tauri::command]
fn convert_to_pdf(markdown: String) -> Result<String, String> {
    let bytes = generate_pdf(&markdown)?;
    Ok(base64::engine::general_purpose::STANDARD.encode(&bytes))
}

/// Copy the last generated temp PDF to a user-chosen destination.
#[tauri::command]
fn save_pdf(destination: String) -> Result<(), String> {
    let src = std::env::temp_dir().join("prep_for_tail_current.pdf");
    std::fs::copy(&src, &destination)
        .map(|_| ())
        .map_err(|e| e.to_string())
}

/// Open a native file-picker, read the chosen file, return its text content (or null).
#[tauri::command]
fn load_markdown_file() -> Result<Option<String>, String> {
    match rfd::FileDialog::new()
        .add_filter("Markdown / Text", &["md", "markdown", "txt"])
        .pick_file()
    {
        None => Ok(None),
        Some(path) => std::fs::read_to_string(&path)
            .map(Some)
            .map_err(|e| e.to_string()),
    }
}

/// Show a native save dialog and write text content to the chosen path.
#[tauri::command]
fn save_text(content: String) -> Result<(), String> {
    let path = rfd::FileDialog::new()
        .add_filter("Text / Markdown", &["txt", "md"])
        .set_file_name("prompt.txt")
        .save_file();
    match path {
        None => Ok(()),
        Some(p) => std::fs::write(&p, content).map_err(|e| e.to_string()),
    }
}

/// Load a YAML config file and return the content of each referenced file.
/// Paths in the YAML may be absolute or relative to the YAML file's directory.
#[tauri::command]
fn load_yaml_config() -> Result<Option<YamlConfigContent>, String> {
    #[derive(serde::Deserialize)]
    struct YamlConfig {
        header: Option<String>,
        body:   Option<String>,
        footer: Option<String>,
        prompt: Option<String>,
    }

    let yaml_path = match rfd::FileDialog::new()
        .add_filter("YAML", &["yaml", "yml"])
        .pick_file()
    {
        None => return Ok(None),
        Some(p) => p,
    };

    let raw = std::fs::read_to_string(&yaml_path).map_err(|e| e.to_string())?;
    let cfg: YamlConfig = serde_yaml::from_str(&raw).map_err(|e| e.to_string())?;

    let base = yaml_path.parent().unwrap_or(std::path::Path::new("."));

    let read = |opt: Option<String>| -> Result<Option<String>, String> {
        match opt {
            None => Ok(None),
            Some(p) => {
                let full = if std::path::Path::new(&p).is_absolute() {
                    std::path::PathBuf::from(&p)
                } else {
                    base.join(&p)
                };
                std::fs::read_to_string(&full)
                    .map(Some)
                    .map_err(|e| format!("{}: {e}", full.display()))
            }
        }
    };

    Ok(Some(YamlConfigContent {
        header: read(cfg.header)?,
        body:   read(cfg.body)?,
        footer: read(cfg.footer)?,
        prompt: read(cfg.prompt)?,
    }))
}

#[derive(serde::Serialize)]
struct YamlConfigContent {
    header: Option<String>,
    body:   Option<String>,
    footer: Option<String>,
    prompt: Option<String>,
}

/// Show a native save-file dialog and return the chosen path (or null).
#[tauri::command]
fn pick_save_path() -> Option<String> {
    rfd::FileDialog::new()
        .add_filter("PDF", &["pdf"])
        .set_file_name("output.pdf")
        .save_file()
        .map(|p| p.to_string_lossy().to_string())
}

// ── PDF generation ────────────────────────────────────────────────────────────

fn generate_pdf(markdown: &str) -> Result<Vec<u8>, String> {
    use typst_as_lib::{TypstEngine, typst_kit_options::TypstKitFontOptions};

    let source = markdown_to_typst(markdown);

    let engine = TypstEngine::builder()
        .main_file(source.as_str())
        .search_fonts_with(
            TypstKitFontOptions::default()
                .include_system_fonts(true)
                .include_embedded_fonts(true),
        )
        .build();

    let doc = engine
        .compile()
        .output
        .map_err(|e| format!("typst: {e:?}"))?;

    let bytes = typst_pdf::pdf(&doc, &Default::default())
        .map_err(|e| format!("typst pdf export: {e:?}"))?;

    let pdf_out = std::env::temp_dir().join("prep_for_tail_current.pdf");
    std::fs::write(&pdf_out, &bytes).map_err(|e| e.to_string())?;

    Ok(bytes)
}

// ── Markdown → Typst conversion ───────────────────────────────────────────────

fn markdown_to_typst(markdown: &str) -> String {
    use comrak::{Arena, Options, parse_document};

    let arena = Arena::new();
    let mut opts = Options::default();
    opts.extension.tasklist = true;
    let root = parse_document(&arena, markdown, &opts);

    // Fonts listed in preference order; typst falls back per-glyph, so
    // Cyrillic text will use DejaVu/Noto when Liberation Sans lacks those glyphs.
    let mut out = String::from(
        "#set page(paper: \"a4\", margin: (x: 2cm, y: 2.5cm))\n\
         #set text(size: 11pt, font: (\"Linux Libertine\", \"Liberation Sans\", \"DejaVu Sans\", \"Noto Sans\"))\n\
         #set par(justify: false, leading: 0.65em)\n\n",
    );
    render_node(root, &mut out, 0);
    out
}

fn render_node<'a>(node: &'a comrak::nodes::AstNode<'a>, out: &mut String, depth: usize) {
    use comrak::nodes::{ListType, NodeValue};

    match &node.data.borrow().value {
        NodeValue::Document => {
            for child in node.children() {
                render_node(child, out, depth);
            }
        }
        NodeValue::Heading(h) => {
            out.push_str(&"=".repeat(h.level as usize));
            out.push(' ');
            for child in node.children() {
                render_node(child, out, depth);
            }
            out.push('\n');
        }
        NodeValue::Paragraph => {
            let children: Vec<_> = node.children().collect();
            // Lone \newpage paragraph → typst page break
            if children.len() == 1 {
                let is_newpage = {
                    let val = children[0].data.borrow();
                    matches!(&val.value, NodeValue::Text(t) if t.trim() == "\\newpage")
                };
                if is_newpage {
                    out.push_str("#pagebreak()\n\n");
                    return;
                }
            }
            for child in children {
                render_node(child, out, depth);
            }
            out.push_str("\n\n");
        }
        NodeValue::Text(text) => {
            // \hfill → typst horizontal fill; \newpage inline → page break.
            // Split on \hfill first; each part may still contain \newpage.
            let parts: Vec<String> = text
                .split("\\hfill")
                .map(|p| {
                    // Replace inline \newpage with a typst page break call
                    p.split("\\newpage")
                        .map(|seg| escape_typst(seg))
                        .collect::<Vec<_>>()
                        .join("#pagebreak()")
                })
                .collect();
            out.push_str(&parts.join("#h(1fr)"));
        }
        NodeValue::Strong => {
            out.push('*');
            for child in node.children() {
                render_node(child, out, depth);
            }
            out.push('*');
        }
        NodeValue::Emph => {
            out.push('_');
            for child in node.children() {
                render_node(child, out, depth);
            }
            out.push('_');
        }
        NodeValue::List(list) => {
            let ordered = matches!(list.list_type, ListType::Ordered);
            let indent = "  ".repeat(depth);

            for item in node.children() {
                // Determine bullet symbol without holding the borrow during child iteration.
                let bullet: &'static str = {
                    let val = item.data.borrow();
                    match &val.value {
                        NodeValue::TaskItem(t) => {
                            if t.symbol.is_some() { "☑ " } else { "☐ " }
                        }
                        _ => if ordered { "+ " } else { "- " },
                    }
                };

                let children: Vec<_> = item.children().collect();
                out.push_str(&indent);
                out.push_str(bullet);

                for (i, child) in children.iter().enumerate() {
                    if let NodeValue::Paragraph = &child.data.borrow().value {
                        for inline in child.children() {
                            render_node(inline, out, depth);
                        }
                        // Tight (single paragraph) items: one newline; loose: two.
                        if children.len() == 1 || i + 1 == children.len() {
                            out.push('\n');
                        } else {
                            out.push_str("\n\n");
                        }
                    } else {
                        render_node(child, out, depth + 1);
                    }
                }
            }
            out.push('\n');
        }
        NodeValue::Item(_) | NodeValue::TaskItem(_) => {
            for child in node.children() {
                render_node(child, out, depth);
            }
        }
        NodeValue::Code(code) => {
            out.push('`');
            out.push_str(&code.literal);
            out.push('`');
        }
        NodeValue::CodeBlock(code) => {
            out.push_str("```");
            out.push_str(code.info.trim());
            out.push('\n');
            out.push_str(&code.literal);
            out.push_str("```\n\n");
        }
        NodeValue::SoftBreak => out.push('\n'),
        NodeValue::LineBreak => out.push_str("\\\n"),
        NodeValue::ThematicBreak => out.push_str("\n#line(length: 100%)\n\n"),
        _ => {
            for child in node.children() {
                render_node(child, out, depth);
            }
        }
    }
}

fn escape_typst(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for c in s.chars() {
        if matches!(c, '#' | '@' | '_' | '*' | '`' | '$' | '[' | ']' | '{' | '}' | '~' | '\\') {
            out.push('\\');
        }
        out.push(c);
    }
    out
}
