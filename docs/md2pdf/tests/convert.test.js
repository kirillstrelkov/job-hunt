import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
import {
  convertMarkdownToPdf,
  createDocDefinition,
  preprocessMarkdown
} from '../src/convert.js';

describe('Syntax Preprocessing', () => {
  it('converts \\break to page break markers', () => {
    const md = 'Line 1\n\\break\nLine 2';
    const processed = preprocessMarkdown(md);
    expect(processed).toContain('page-break-before: always');
  });

  it('converts \\hfill to borderless alignment tables', () => {
    const md = 'Title \\hfill 2026';
    const processed = preprocessMarkdown(md);
    expect(processed).toContain('<table');
    expect(processed).toContain('text-align: right;');
  });
});

describe('Document Definition & Typography', () => {
  const exampleMdPath = path.join(__dirname, '../public/example.md');
  const markdown = fs.readFileSync(exampleMdPath, 'utf8');

  it('strips <hr> tags to prevent horizontal lines', () => {
    const docDef = createDocDefinition('# Header\n---\n## Body');
    // Ensure no canvas lines were generated from hr
    const hasCanvasLine = docDef.content.some(item => item && item.canvas);
    expect(hasCanvasLine).toBe(false);
  });

  it('filters out empty whitespace text nodes', () => {
    const docDef = createDocDefinition(markdown);
    const emptyNodes = docDef.content.filter(
      item => typeof item.text === 'string' && item.text.trim() === ''
    );
    expect(emptyNodes.length).toBe(0);
  });

  it('enforces black un-underlined hyperlinks', () => {
    const docDef = createDocDefinition('[Link](https://example.com)');
    function checkLinks(node) {
      if (!node) return;
      if (Array.isArray(node)) return node.forEach(checkLinks);
      if (node.link) {
        expect(node.color).toBe('#000000');
        expect(node.decoration).toBeUndefined();
      }
      if (node.text && typeof node.text === 'object') checkLinks(node.text);
    }
    checkLinks(docDef.content);
  });

  it('maps pageBreakBefore to pageBreak in doc definition nodes', () => {
    const docDef = createDocDefinition('Before break\n\n\\break\n\nAfter break');
    const breakNode = docDef.content.find(item => item && item.pageBreak === 'before');
    expect(breakNode).toBeDefined();
    expect(breakNode.pageBreak).toBe('before');
  });

  it('configures A4 geometry and compact margins', () => {
    const docDef = createDocDefinition(markdown);
    expect(docDef.pageSize).toBe('A4');
    expect(docDef.pageOrientation).toBe('portrait');
    expect(docDef.pageMargins).toEqual([42.5, 34, 42.5, 34]);
    expect(docDef.defaultStyle.fontSize).toBe(9.5);
    expect(docDef.defaultStyle.lineHeight).toBe(1.15);
  });
});

describe('PDF Generation & pdftotext Layout Analysis', () => {
  const exampleMdPath = path.join(__dirname, '../public/example.md');
  const outputPdfPath = path.join(__dirname, '../output.pdf');
  const markdown = fs.readFileSync(exampleMdPath, 'utf8');

  it('converts example.md to a valid PDF file', async () => {
    const res = await convertMarkdownToPdf(markdown, outputPdfPath);
    expect(res).toBe(outputPdfPath);
    expect(fs.existsSync(outputPdfPath)).toBe(true);

    const stats = fs.statSync(outputPdfPath);
    expect(stats.size).toBeGreaterThan(10000);
  });

  it('extracts exactly 2 pages with pdftotext', () => {
    const extractedText = execFileSync('pdftotext', [outputPdfPath, '-'], {
      encoding: 'utf8'
    });
    const pages = extractedText.split('\f').filter(p => p.trim().length > 0);
    expect(pages.length).toBe(2);
  });

  it('ensures \\hfill is not available on any page', () => {
    const extractedText = execFileSync('pdftotext', [outputPdfPath, '-'], {
      encoding: 'utf8'
    });
    const pages = extractedText.split('\f').filter(p => p.trim().length > 0);
    expect(pages.length).toBeGreaterThan(0);
    pages.forEach((pageText, idx) => {
      expect(pageText, `Page ${idx + 1} contains literal \\hfill`).not.toContain('\\hfill');
    });
  });

  it('ensures \\break is not available on any page', () => {
    const extractedText = execFileSync('pdftotext', [outputPdfPath, '-'], {
      encoding: 'utf8'
    });
    const pages = extractedText.split('\f').filter(p => p.trim().length > 0);
    expect(pages.length).toBeGreaterThan(0);
    pages.forEach((pageText, idx) => {
      expect(pageText, `Page ${idx + 1} contains literal \\break`).not.toContain('\\break');
    });
  });

  it('ensures Junior Developer is not available on first page but available on second page', () => {
    const extractedText = execFileSync('pdftotext', [outputPdfPath, '-'], {
      encoding: 'utf8'
    });
    const pages = extractedText.split('\f').filter(p => p.trim().length > 0);
    expect(pages.length).toBe(2);
    const p1 = pages[0];
    const p2 = pages[1];

    expect(p1).not.toContain('Junior Developer');
    expect(p2).toContain('Junior Developer');
  });

  it('verifies Page 1 ends with Web Developer and footer 1', () => {
    const extractedText = execFileSync('pdftotext', [outputPdfPath, '-'], {
      encoding: 'utf8'
    });
    const pages = extractedText.split('\f').filter(p => p.trim().length > 0);
    const p1 = pages[0];

    expect(p1).toContain('John Doe');
    expect(p1).toContain('Berlin, Germany');
    expect(p1).toContain('Work Experience');
    expect(p1).toContain('Senior Software Engineer');
    expect(p1).toContain('Web Developer');
    expect(p1).toContain('Creative Code Agency');
    expect(p1.trim().endsWith('1')).toBe(true);
  });

  it('verifies Page 2 starts with Junior Developer and ends with Languages and footer 2', () => {
    const extractedText = execFileSync('pdftotext', [outputPdfPath, '-'], {
      encoding: 'utf8'
    });
    const pages = extractedText.split('\f').filter(p => p.trim().length > 0);
    const p2 = pages[1];

    expect(p2).toContain('Junior Developer');
    expect(p2).toContain('Data Systems B.V.');
    expect(p2).toContain('Personal Projects');
    expect(p2).toContain('Cloud-Native API Gateway');
    expect(p2).toContain('Courses and Certificates');
    expect(p2).toContain('Education');
    expect(p2).toContain('Languages');
    expect(p2).toContain('English: Native, German: B2 (Upper Intermediate), Spanish: A2 (Elementary)');
    expect(p2.trim().endsWith('2')).toBe(true);
  });
});
