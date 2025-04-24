import { useState, useRef, useEffect } from "react";
import {
  FileText,
  Sparkles,
  Brain,
  Code,
  PenTool,
  Bot,
  Pin,
  SendHorizontal,
  Edit,
  Download,
  Copy,
  MessageSquare
} from "lucide-react";
import { useChatHistory } from "../context/ChatHistoryContext.jsx";
import LeftDrawer from "./LeftDrawer";
import ChatMessage from "./ChatMessage"; // Import our new component
import "./ResearchPaperGenerator.css";
import "./ResearchPaperStyles.css";
import "./ChatMessageStyles.css"; // Import new styles
import { marked } from 'marked';
import DOMPurify from 'dompurify';

// Configure marked with better defaults
marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: true
});

const ResearchPaperGenerator = () => {
  // Access chat history context
  const { addChat, updateMessages, getCurrentChat, selectedChatId, selectChat } =
    useChatHistory();

  // All state and refs
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [showPaper, setShowPaper] = useState(false);
  const [isEditingPaper, setIsEditingPaper] = useState(false);
  const [paperContent, setPaperContent] = useState("");
  const [paperHtml, setPaperHtml] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [layoutChanged, setLayoutChanged] = useState(false);
  const [, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(false);

  // Input Section states
  const [isSourceMenuOpen, setIsSourceMenuOpen] = useState(false);
  const [selectedSource, setSelectedSource] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  //const fileInputRef = useRef(null);
  const chatContainerRef = useRef(null);
  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);
  const paperContentRef = useRef(null);

  // Add refs for intervals to properly clean them up
  const stepIntervalRef = useRef(null);
  const messageIntervalRef = useRef(null);
  const pollIntervalRef = useRef(null);

  const processingSteps = [
    { text: "Analyzing your code...", icon: <Code /> },
    { text: "Understanding the structure...", icon: <Brain /> },
    { text: "Generating research paper...", icon: <PenTool /> },
    { text: "Humanizing content...", icon: <Bot /> },
  ];

  // Function to convert markdown to HTML
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

  // Generate HTML when paperContent changes
  useEffect(() => {
    if (paperContent) {
      const html = convertMarkdownToHtml(paperContent);
      setPaperHtml(html);
    }
  }, [paperContent]);

  // Handle dark mode toggle
  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    if (!darkMode) {
      document.body.classList.add("dark-mode");
    } else {
      document.body.classList.remove("dark-mode");
    }
  };

  // Initialize dark mode from localStorage
  useEffect(() => {
    const savedDarkMode = localStorage.getItem("darkMode") === "true";
    setDarkMode(savedDarkMode);
    if (savedDarkMode) {
      document.body.classList.add("dark-mode");
    }
  }, []);

  // Save dark mode preference to localStorage
  useEffect(() => {
    localStorage.setItem("darkMode", darkMode);
  }, [darkMode]);

  // Auto scroll to bottom when new message arrives
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }

    // Also scroll the messagesEndRef into view for smooth scrolling
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Reset state when a chat is selected
  useEffect(() => {
    if (selectedChatId) {
      const currentChat = getCurrentChat();
      
      // Reset messages
      if (currentChat) {
        setChatMessages(currentChat.messages || []);
        setLayoutChanged(true);
        
        // Check if this is a new chat with no messages
        if (currentChat.messages.length === 0) {
          // Reset all UI state for a fresh chat
          setShowPaper(false);
          setIsEditingPaper(false);
          setPaperContent("");
          setPaperHtml("");
          setIsProcessing(false);
          setIsGenerating(false);
          setError(null);
        } else {
          // Check if the existing chat has a paper generated
          const paperMessage = currentChat.messages.find(
            (msg) => msg.role === "assistant" && msg.paperContent
          );

          if (paperMessage) {
            setPaperContent(paperMessage.paperContent);
            setPaperHtml(convertMarkdownToHtml(paperMessage.paperContent));
            // Don't automatically show the paper when switching chats
            setShowPaper(false);
            setIsEditingPaper(false);
          } else {
            // No paper in this chat
            setShowPaper(false);
            setPaperContent("");
            setPaperHtml("");
          }
        }
      }
    }
  }, [selectedChatId, getCurrentChat]);

  // Auto-layout when a chat is selected or started
  useEffect(() => {
    if (selectedChatId) {
      setLayoutChanged(true);
    }
  }, [selectedChatId]);

  // const handleSourceSelect = (source) => {
  //   setSelectedSource(source);
  //   setIsSourceMenuOpen(false);
  // };

  // const handleFileUpload = (e) => {
  //   const files = e.target.files;
  //   if (files) {
  //     console.log("Uploaded files:", files);
  //     Array.from(files).forEach((file) => {
  //       console.log("File:", file.name, "Path:", file.webkitRelativePath);
  //     });
  //   }
  // };

  // Open paper in full view
  const handleOpenFullPaper = () => {
    setShowPaper(true);
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 200) + "px";
    }
  }, [inputValue]);

  // Add cleanup for all intervals when component unmounts
  useEffect(() => {
    const stepInterval = stepIntervalRef.current;
    const messageInterval = messageIntervalRef.current;
    const pollInterval = pollIntervalRef.current;
  
    return () => {
      if (stepInterval) clearInterval(stepInterval);
      if (messageInterval) clearInterval(messageInterval);
      if (pollInterval) clearInterval(pollInterval);
    };
  }, []);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isGenerating) return;

    const inputData = {
      prompt: inputValue,
      source: selectedSource,
      url: sourceUrl,
      timestamp: new Date().toLocaleTimeString(),
    };

    // Create a new chat if none is selected
    if (!selectedChatId) {
      const cleanInput = inputValue.replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
      const chatTopic = cleanInput.substring(0, 50) + (cleanInput.length > 50 ? "..." : "");
      const newChatId = addChat(chatTopic);
      selectChat(newChatId);
    }

    // Call the API integration function
    handleFormSubmission(inputData);

    // Change to two-column layout
    setLayoutChanged(true);

    // Clear the input
    setInputValue("");
    setSourceUrl("");
    setSelectedSource(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFormSubmission = async (inputData) => {
    // Clear any existing errors
    setError(null);

    // Clear any previous intervals
    if (stepIntervalRef.current) clearInterval(stepIntervalRef.current);
    if (messageIntervalRef.current) clearInterval(messageIntervalRef.current);
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    setIsProcessing(true);
    setIsGenerating(true);
    setCurrentStep(0); // Reset step counter

    // Initialize with user and loading messages
    const newUserMessage = { role: "user", text: inputData.prompt };
    const loadingMessage = {
      role: "system",
      text: "Generating your research paper. Please wait...",
    };

    const updatedMessages = [...chatMessages, newUserMessage, loadingMessage];
    setChatMessages(updatedMessages);

    // Update in context
    updateMessages(updatedMessages);

    setShowPaper(false);
    setIsEditingPaper(false);

    // Start the processing steps animation
    let step = 0;
    stepIntervalRef.current = setInterval(() => {
      if (step < processingSteps.length - 1) {
        step++;
        setCurrentStep(step);
      } else {
        clearInterval(stepIntervalRef.current);
        stepIntervalRef.current = null;
      }
    }, 2000);

    try {
      // Prepare the request data
      const requestData = {
        topic: inputData.prompt,
        sections: [
          "Abstract",
          "Introduction",
          "Literature Review",
          "Methodology",
          "Results",
          "Discussion",
          "Conclusion",
          "References",
        ],
        wordCount: 3000,
        sourceType: inputData.source || null,
        sourceUrl: inputData.url || null,
        repoUrl: inputData.source === "github" ? inputData.url : null,
      };

      console.log("Sending request data:", JSON.stringify(requestData));

      // Make API call to the backend
      const response = await fetch("/api/research/generate-paper", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        console.error(
          "Server response not OK:",
          response.status,
          response.statusText
        );
        let errorMessage = "Failed to generate paper";

        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorData.detail || errorMessage;
        } catch (parseError) {
          console.error("Error parsing error response:", parseError);
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log("API response:", data);

      // If the paper is being processed, poll for updates
      if (data.status === "processing") {
        const documentId = data.document_id;

        // Update the loading message
        const newMessages = [
          ...chatMessages.filter((msg) => msg.role !== "system"),
          newUserMessage,
          {
            role: "system",
            text: "Your paper is being generated. This may take a few minutes.",
          },
        ];

        setChatMessages(newMessages);
        updateMessages(newMessages);

        // Poll for updates
        pollIntervalRef.current = setInterval(async () => {
          try {
            const statusResponse = await fetch(
              `/api/research/paper/${documentId}`
            );

            if (!statusResponse.ok) {
              throw new Error(`Status check failed: ${statusResponse.status}`);
            }

            const statusData = await statusResponse.json();
            console.log("Poll response:", statusData);

            if (statusData.status === "success") {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;

              if (statusData.paper) {
                handlePaperGenerated(statusData.paper, inputData.prompt);
              } else {
                setError("Paper content is empty");
                const errorMessages = [
                  ...chatMessages.filter((msg) => msg.role !== "system"),
                  newUserMessage,
                  {
                    role: "system",
                    text: "Error: Paper content is empty. Please try again with a different topic or repository.",
                  },
                ];
                setChatMessages(errorMessages);
                updateMessages(errorMessages);
                setIsProcessing(false);
                setIsGenerating(false);
              }
            } else if (statusData.status === "error") {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
              throw new Error(statusData.message || "Unknown error occurred");
            }
            // Continue polling if status is still processing
          } catch (pollError) {
            console.error("Polling error:", pollError);
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;

            setError(pollError.message);
            const errorMessages = [
              ...chatMessages.filter((msg) => msg.role !== "system"),
              newUserMessage,
              {
                role: "system",
                text: `Error: ${pollError.message}. Please try again.`,
              },
            ];
            setChatMessages(errorMessages);
            updateMessages(errorMessages);
            setIsProcessing(false);
            setIsGenerating(false);
          }
        }, 5000); // Poll every 5 seconds
      } else if (data.status === "success") {
        // Paper was generated immediately
        if (data.paper) {
          handlePaperGenerated(data.paper, inputData.prompt);
        } else {
          setError("Paper content is empty");
          const errorMessages = [
            ...chatMessages.filter((msg) => msg.role !== "system"),
            newUserMessage,
            {
              role: "system",
              text: "Error: Paper content is empty. Please try again with a different topic or repository.",
            },
          ];
          setChatMessages(errorMessages);
          updateMessages(errorMessages);
          setIsProcessing(false);
          setIsGenerating(false);
        }
      } else {
        throw new Error(data.message || "Unknown error occurred");
      }
    } catch (error) {
      console.error("Error generating paper:", error);

      setError(error.message);
      const errorMessages = [
        ...chatMessages.filter((msg) => msg.role !== "system"),
        newUserMessage,
        {
          role: "error",
          text: `Error: ${error.message}. Please try again.`,
        },
      ];
      setChatMessages(errorMessages);
      updateMessages(errorMessages);
      setIsProcessing(false);
      setIsGenerating(false);
    }
  };

  const handlePaperGenerated = (paperText) => {
    setIsProcessing(false);
    setIsGenerating(false);
  
    // Set the paper content
    setPaperContent(paperText);
    
    // Convert markdown to HTML
    const html = convertMarkdownToHtml(paperText);
    setPaperHtml(html);
  
    // Create a new assistant message with the paper
    const assistantMessage = {
      role: "assistant",
      text: `Here is your generated research paper:`,
      paperContent: paperText,
      timestamp: new Date().toISOString()
    };
  
    // Update chat messages by removing the loading message and adding the assistant response
    const newMessages = [
      ...chatMessages.filter((msg) => msg.role !== "system"),
      assistantMessage,
    ];
    setChatMessages(newMessages);
    updateMessages(newMessages);
  
    // Automatically show the paper in full view
    setShowPaper(true);
    setIsEditingPaper(false);
  };

  const handleEditPaper = () => {
    setIsEditingPaper(true);
  };

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(paperContent).then(
      () => {
        // Create a system message to inform the user
        const systemMessage = {
          role: "system",
          text: "Paper content copied to clipboard",
        };
        const newMessages = [...chatMessages, systemMessage];
        setChatMessages(newMessages);
        updateMessages(newMessages);
      },
      (err) => {
        console.error("Failed to copy text: ", err);
        setError("Failed to copy to clipboard: " + err.message);
      }
    );
  };

  const handleSavePaper = () => {
    try {
      // For HTML saving
      const htmlOutput = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Research Paper</title>
  <style>
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
    pre {
      background-color: #f5f5f5;
      padding: 10px;
      border-radius: 5px;
      overflow: auto;
    }
    code {
      font-family: Consolas, Monaco, monospace;
      background-color: #f5f5f5;
      padding: 2px 4px;
      border-radius: 3px;
    }
    blockquote {
      border-left: 4px solid #ccc;
      padding-left: 16px;
      margin-left: 0;
      color: #666;
    }
    .paper-container {
      border: 1px solid #ddd;
      border-radius: 5px;
      padding: 30px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    @media print {
      body { max-width: none; margin: 0; padding: 0; }
      .paper-container { border: none; box-shadow: none; padding: 0; }
    }
  </style>
</head>
<body>
  <div class="paper-container">
    ${paperHtml}
  </div>
</body>
</html>
      `;

      const blob = new Blob([htmlOutput], { type: "text/html" });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = "research-paper.html";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Create a system message to inform the user
      const systemMessage = {
        role: "system",
        text: "Research paper saved as research-paper.html",
      };
      const newMessages = [...chatMessages, systemMessage];
      setChatMessages(newMessages);
      updateMessages(newMessages);
    } catch (error) {
      console.error("Error saving paper:", error);
      setError("Failed to save paper: " + error.message);
    }
  };

  return (
    <div className={`container ${darkMode ? "dark-mode" : ""}`}>
      <div className="main-content">
        {layoutChanged && (
          <LeftDrawer darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        )}
  
        <div className={`right-column ${!layoutChanged ? "no-drawer" : ""}`}>
          {!layoutChanged && (
            <header className="header">
              <div className="logo">
                <FileText className="logo-icon" />
                <span>ResearchAI</span>
              </div>
              <h1>Research Paper Generator</h1>
              <p>
                Generate comprehensive research papers from any source. Input
                your topic or provide a code repository to get started.
              </p>
            </header>
          )}
  
          {isProcessing ? (
            <div className="processing-container">
              {processingSteps.map((step, index) => (
                <div
                  key={index}
                  className={`processing-step ${
                    index === currentStep ? "active" : ""
                  } ${index < currentStep ? "completed" : ""}`}
                >
                  <div className="processing-icon">{step.icon}</div>
                  <div className="processing-text">{step.text}</div>
                </div>
              ))}
            </div>
          ) : showPaper ? (
            <div className="paper-container">
              <h2>Research Paper</h2>
              
              {isEditingPaper ? (
                <>
                  <textarea
                    className="paper-content-editor"
                    value={paperContent}
                    onChange={(e) => setPaperContent(e.target.value)}
                    style={{
                      width: "100%",
                      minHeight: "70vh", // Increased height
                      padding: "30px",   // More padding
                      border: "1px solid #ddd",
                      borderRadius: "4px",
                      fontFamily: "'Times New Roman', Times, serif", // IEEE style font
                      fontSize: "16px",  // Larger font
                      lineHeight: "1.6",
                      resize: "vertical"
                    }}
                  />
                  
                  <div className="paper-actions">
                    <button
                      className="submit-button primary"
                      onClick={() => {
                        setIsEditingPaper(false);
                        
                        // Update HTML when saving edits
                        const html = convertMarkdownToHtml(paperContent);
                        setPaperHtml(html);
                        
                        // Create a system message to inform user of save
                        const systemMessage = {
                          role: "system",
                          text: "Paper edits saved",
                        };
                        const newMessages = [...chatMessages, systemMessage];
                        setChatMessages(newMessages);
                        updateMessages(newMessages);
                      }}
                    >
                      Save Edits
                    </button>
                    
                    <button
                      className="submit-button secondary"
                      onClick={() => {
                        // Discard changes and restore original content
                        setIsEditingPaper(false);
                        
                        // Get original content from chat
                        const paperMessage = chatMessages.find(
                          (msg) => msg.role === "assistant" && msg.paperContent
                        );
                        
                        if (paperMessage) {
                          setPaperContent(paperMessage.paperContent);
                          setPaperHtml(convertMarkdownToHtml(paperMessage.paperContent));
                        }
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </>
              ) : (
                <>
                  {/* HTML Paper Content Display */}
                  <div 
                    className="paper-content-display"
                    ref={paperContentRef}
                    dangerouslySetInnerHTML={{ __html: paperHtml }}
                  />
                  
                  <div className="paper-actions">
                    <div className="paper-action-buttons">
                      <button 
                        className="action-button"
                        onClick={handleEditPaper}
                        title="Edit Paper"
                      >
                        <Edit size={16} />
                        <span>Edit</span>
                      </button>
                      
                      <button 
                        className="action-button"
                        onClick={handleCopyToClipboard}
                        title="Copy to Clipboard"
                      >
                        <Copy size={16} />
                        <span>Copy</span>
                      </button>
                      
                      <button 
                        className="action-button"
                        onClick={handleSavePaper}
                        title="Download Paper as HTML"
                      >
                        <Download size={16} />
                        <span>Download HTML</span>
                      </button>
                      
                      <button
                        className="action-button secondary"
                        onClick={() => setShowPaper(false)}
                        title="Return to Chat"
                      >
                        <MessageSquare size={16} />
                        <span>Chat</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ) : (
            <>
              <div
                className="chat-container"
                ref={chatContainerRef}
                style={{ display: chatMessages.length > 0 ? "flex" : "none" }}
              >
                {chatMessages.map((message, index) => (
                  <ChatMessage 
                    key={index} 
                    message={message} 
                    onClick={handleOpenFullPaper}
                  />
                ))}
                {isGenerating && (
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
  
              {chatMessages.length === 0 && (
                <div className="empty-chat">
                  <div className="empty-chat-content">
                    <Sparkles size={48} className="empty-chat-icon" />
                    <h1>Generate Research Papers</h1>
                    <p>
                      Enter your topic or provide a code repository to generate a research
                      paper
                    </p>
                  </div>
                </div>
              )}
            </>
          )}
  
          <div
            className={`input-section-container ${
              isGenerating ? "generating" : ""
            } ${!layoutChanged ? "no-drawer" : ""}`}
          >
            <form onSubmit={handleSubmit}>
              <div className="input-container">
                {selectedSource && (
                  <button
                    type="button"
                    className="source-button"
                    onClick={() => setSelectedSource(null)}
                    title="Remove source"
                  >
                    <Pin size={18} />
                  </button>
                )}
  
                <textarea
                  ref={textareaRef}
                  className="input-field"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter a topic to start generating a research paper..."
                  rows={1}
                />
  
                <button
                  type="button"
                  className="source-button"
                  onClick={() => setIsSourceMenuOpen(!isSourceMenuOpen)}
                  title="Add source"
                >
                  <Pin size={18} />
                </button>
  
                <button
                  type="submit"
                  className="send-button"
                  disabled={!inputValue.trim() || isGenerating}
                >
                  <SendHorizontal size={18} />
                </button>
              </div>
  
              {/* Rest of the input form code remains the same */}
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearchPaperGenerator;