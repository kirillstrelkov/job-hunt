export function toPlainText(text: string): string {
  // Remove HTML tags
  text = text.replace(/<[^>]+>/g, "");
  // Remove markdown links: [label](url) → label
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  // Remove fenced code blocks
  text = text.replace(/```[\s\S]*?```/g, "");
  // Remove inline code
  text = text.replace(/`([^`]+)`/g, "$1");
  // Remove ATX headers
  text = text.replace(/^#{1,6}\s+/gm, "");
  // Remove bold/italic markers
  text = text.replace(/(\*{1,3}|_{1,3})(.+?)\1/g, "$2");
  // Remove horizontal rules
  text = text.replace(/^[-*_]{3,}\s*$/gm, "");
  // Collapse excess blank lines
  text = text.replace(/\n{3,}/g, "\n\n");
  return text.trim();
}
