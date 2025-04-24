// markdown-to-html.js
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import hljs from 'highlight.js';
import 'highlight.js/styles/github.css';
import PropTypes from 'prop-types';


// Configure marked with syntax highlighting
marked.setOptions({
  highlight: function(code, language) {
    if (language && hljs.getLanguage(language)) {
      try {
        return hljs.highlight(code, { language }).value;
      } catch (err) {
        console.error('Highlight.js error:', err);
      }
    }
    return code;
  },
  breaks: true,
  gfm: true,
  headerIds: true,
  langPrefix: 'hljs language-'
});

/**
 * Converts markdown content to sanitized HTML
 * @param {string} markdown - The markdown content to convert
 * @returns {string} - The sanitized HTML string
 */
export const convertMarkdownToHtml = (markdown) => {
  if (!markdown) return '';
  
  try {
    // Convert markdown to HTML using marked
    const rawHtml = marked.parse(markdown);
    
    // Sanitize HTML to prevent XSS attacks
    const sanitizedHtml = DOMPurify.sanitize(rawHtml, {
      USE_PROFILES: { html: true },
      ADD_ATTR: ['target', 'rel']
    });
    
    return sanitizedHtml;
  } catch (error) {
    console.error('Error converting markdown to HTML:', error);
    return `<p>Error rendering content: ${error.message}</p>`;
  }
};

/**
 * React component that renders markdown as HTML
 * @param {Object} props - Component props
 * @param {string} props.markdown - The markdown content to render
 * @param {Object} props.className - Optional CSS class for the container
 * @returns {React.Component} - A React component with rendered HTML
 */
export const MarkdownRenderer = ({ markdown, className = '' }) => {
  if (!markdown) return null;
  
  const htmlContent = convertMarkdownToHtml(markdown);
  
  return (
    <div 
      className={`markdown-content ${className}`}
      dangerouslySetInnerHTML={{ __html: htmlContent }}
    />
  );
};

/**
 * Generates a complete standalone HTML document from markdown
 * @param {string} markdown - The markdown content
 * @param {Object} options - Additional options
 * @param {string} options.title - Document title
 * @param {string} options.cssStyles - Additional CSS styles
 * @returns {string} - Complete HTML document as string
 */
export const generateCompleteHtml = (markdown, options = {}) => {
  const { 
    title = 'Research Paper', 
    cssStyles = '' 
  } = options;
  
  const htmlContent = convertMarkdownToHtml(markdown);
  
  // Base CSS for the paper
  const baseStyles = `
    body {
      font-family: 'Times New Roman', Times, serif;
      line-height: 1.6;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }
    h1 { font-size: 24px; margin-top: 20px; }
    h2 { font-size: 20px; margin-top: 18px; }
    h3 { font-size: 16px; margin-top: 16px; }
    h4 { font-size: 14px; margin-top: 14px; }
    p { margin: 10px 0; }
    blockquote {
      border-left: 4px solid #ccc;
      padding-left: 16px;
      margin-left: 0;
      color: #666;
    }
    pre {
      background-color: #f5f5f5;
      padding: 10px;
      border-radius: 5px;
      overflow: auto;
    }
    code {
      font-family: Consolas, Monaco, 'Andale Mono', monospace;
      background-color: #f5f5f5;
      padding: 2px 4px;
      border-radius: 3px;
    }
    pre code {
      padding: 0;
      background: transparent;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      margin: 20px 0;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 8px 12px;
      text-align: left;
    }
    th {
      background-color: #f5f5f5;
    }
    .paper-container {
      border: 1px solid #ddd;
      border-radius: 5px;
      padding: 30px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    @media print {
      body {
        max-width: none;
        margin: 0;
        padding: 0;
      }
      .paper-container {
        border: none;
        box-shadow: none;
        padding: 0;
      }
    }
    /* Apply custom styles */
    ${cssStyles}
  `;
  
  // Complete HTML document
  const htmlDocument = `
  <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>${baseStyles}</style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css">
  </head>
  <body>
    <div class="paper-container">
      ${htmlContent}
    </div>
  </body>
  </html>
  `;
  
  return htmlDocument;
};

export default {
  convertMarkdownToHtml,
  MarkdownRenderer,
  generateCompleteHtml
};

MarkdownRenderer.propTypes = {
    markdown: PropTypes.string.isRequired,
    className: PropTypes.string
  };
  