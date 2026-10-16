import React, { useMemo } from 'react';
import { marked } from 'marked';

// Configure marked for GitHub Flavored Markdown
marked.setOptions({
  gfm: true,
  breaks: true,
});

export default function MarkdownView({ content, style = {} }) {
  const htmlContent = useMemo(() => {
    if (!content) return '';
    try {
      // Clean up any double-escaped markdown or rogue formatting
      return marked.parse(content);
    } catch (e) {
      console.error('Markdown parsing error:', e);
      return content;
    }
  }, [content]);

  return (
    <div
      className="markdown-content"
      style={{
        lineHeight: 1.6,
        fontSize: '0.925rem',
        color: '#f1f5f9',
        ...style
      }}
      dangerouslySetInnerHTML={{ __html: htmlContent }}
    />
  );
}
