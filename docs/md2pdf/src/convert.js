'use strict';

const fs = require('fs');
const path = require('path');
const { marked } = require('marked');
const htmlToPdfmake = require('html-to-pdfmake');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

const pdfMake = require('pdfmake/build/pdfmake');
const vfsFonts = require('pdfmake/build/vfs_fonts');
pdfMake.vfs = vfsFonts.pdfMake ? vfsFonts.pdfMake.vfs : vfsFonts;

const {
  preprocessMarkdown,
  cleanPdfNodes,
  defaultStyles,
  buildDocDef
} = require('./core');

marked.use({
  gfm: true,
  breaks: true
});

function createDocDefinition(markdown) {
  const preprocessed = preprocessMarkdown(markdown, marked);
  const rawHtml = marked.parse(preprocessed);
  const cleanHtml = rawHtml.replace(/<hr\s*\/?>/gi, '');

  const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
  let pdfContent = htmlToPdfmake(cleanHtml, {
    window: dom.window,
    tableAutoSize: true,
    defaultStyles: defaultStyles
  });

  pdfContent = cleanPdfNodes(pdfContent);
  return buildDocDef(pdfContent);
}

function convertMarkdownToPdf(markdown, outputPath) {
  return new Promise((resolve, reject) => {
    try {
      const docDef = createDocDefinition(markdown);
      const pdfDoc = pdfMake.createPdf(docDef);

      pdfDoc.getBuffer((buffer) => {
        try {
          if (!buffer) {
            return reject(new Error('PDF generation produced empty buffer'));
          }
          if (outputPath) {
            fs.writeFileSync(outputPath, buffer);
            resolve(outputPath);
          } else {
            resolve(buffer);
          }
        } catch (writeErr) {
          reject(writeErr);
        }
      });
    } catch (err) {
      reject(err);
    }
  });
}

module.exports = {
  convertMarkdownToPdf,
  createDocDefinition,
  preprocessMarkdown,
  cleanPdfNodes,
  defaultStyles,
  buildDocDef
};
