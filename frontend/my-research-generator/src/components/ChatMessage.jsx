import DOMPurify from 'dompurify';
import { marked } from 'marked';
import { FileText } from 'lucide-react';
import PropTypes from 'prop-types';
import { useState, useEffect } from 'react';

// Configure marked with better defaults
marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: true
});

// Convert markdown to HTML safely
const convertMarkdownToHtml = (markdown) => {
  if (!markdown) return '';
  
  try {
    // Convert markdown to HTML
    const rawHtml = marked.parse(markdown);
    
    // Sanitize HTML to prevent XSS attacks
    const sanitizedHtml = DOMPurify.sanitize(rawHtml);
    
    return sanitizedHtml;
  } catch (error) {
    console.error('Error converting markdown to HTML:', error);
    return `<p>Error rendering content: ${error.message}</p>`;
  }
};

/**
 * ChatMessage component that handles different message types including paper content
 */
const ChatMessage = ({ message, onClick }) => {
  const [paperHtml, setPaperHtml] = useState('');
  
  // Convert paper content to HTML when the message has paperContent
  useEffect(() => {
    if (message.paperContent) {
      const html = convertMarkdownToHtml(message.paperContent);
      setPaperHtml(html);
    }
  }, [message.paperContent]);

  // For system or error messages, render normally
  if (message.role === 'system' || message.role === 'error') {
    return <div className={`chat-message ${message.role}`}>{message.text}</div>;
  }
  
  // For user messages, render normally
  if (message.role === 'user') {
    return <div className={`chat-message ${message.role}`}>{message.text}</div>;
  }
  
  // For assistant messages with paper content
  if (message.role === 'assistant' && message.paperContent) {
    return (
      <div className={`chat-message ${message.role} paper-message`}>
        <div className="paper-full-content">
          <div className="paper-header">
            <FileText size={16} />
            <span>Research Paper</span>
          </div>
          
          {/* Display the full paper as HTML */}
          <div 
            className="chat-paper-content"
            dangerouslySetInnerHTML={{ __html: paperHtml }}
          />
          
          <button 
            className="view-full-paper-button"
            onClick={onClick}
          >
            Open in Full View
          </button>
        </div>
      </div>
    );
  }
  
  // For regular assistant messages
  return <div className={`chat-message ${message.role}`}>{message.text}</div>;
};

ChatMessage.propTypes = {
    message: PropTypes.shape({
      role: PropTypes.string.isRequired,
      text: PropTypes.string,
      paperContent: PropTypes.string,
    }).isRequired,
    onClick: PropTypes.func,
  };
  

export default ChatMessage;