import { useState, useRef, useEffect } from 'react';
import { FileText, Sparkles, Brain, Code, PenTool, Bot, Pin, Github, Folder, Send } from 'lucide-react';
import './ResearchPaperGenerator.css';

const ResearchPaperGenerator = () => {
  // All your state and refs remain the same
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [showPaper, setShowPaper] = useState(false);
  const [paperContent, setPaperContent] = useState(`## Research Paper Generated

This is an auto-generated research paper based on your input. 
Feel free to modify and customize the content as needed.


### Introduction

### Methodology

### Results

### Conclusion`);
  const [chatMessages, setChatMessages] = useState([]);
  // Removed unused previewContent state
  // Removed unused userPromptHistory state
  const [layoutChanged, setLayoutChanged] = useState(false);
  const [synopsis, setSynopsis] = useState('');
  const [error, setError] = useState(null);
  
  // Input Section states
  const [isSourceMenuOpen, setIsSourceMenuOpen] = useState(false);
  const [selectedSource, setSelectedSource] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const fileInputRef = useRef(null);
  const chatContainerRef = useRef(null);
  const textareaRef = useRef(null);
  
  // Add refs for intervals to properly clean them up
  const stepIntervalRef = useRef(null);
  const messageIntervalRef = useRef(null);
  const pollIntervalRef = useRef(null);

  const processingSteps = [
    { text: "Analyzing your code...", icon: <Code /> },
    { text: "Understanding the structure...", icon: <Brain /> },
    { text: "Generating research paper...", icon: <PenTool /> },
    { text: "Humanizing content...", icon: <Bot /> }
  ];

  const handleSourceSelect = (source) => {
    setSelectedSource(source);
    setIsSourceMenuOpen(false);
  };

  const handleFileUpload = (e) => {
    const files = e.target.files;
    if (files) {
      console.log('Uploaded files:', files);
      Array.from(files).forEach(file => {
        console.log('File:', file.name, 'Path:', file.webkitRelativePath);
      });
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputValue]);

  // Add cleanup for all intervals when component unmounts
  useEffect(() => {
    return () => {
      // Clean up all intervals on unmount
      if (stepIntervalRef.current) clearInterval(stepIntervalRef.current);
      if (messageIntervalRef.current) clearInterval(messageIntervalRef.current);
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isGenerating) return;
    
    const inputData = {
      prompt: inputValue,
      source: selectedSource,
      url: sourceUrl,
      timestamp: new Date().toLocaleTimeString()
    };
    
    // Call the API integration function
    handleFormSubmission(inputData);
    
    // Change to two-column layout
    setLayoutChanged(true);
    
    // Clear the input
    setInputValue('');
    setSourceUrl('');
    setSelectedSource(null);
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
    
    // Initialize with a loading message
    setChatMessages([
      { role: 'system', text: 'Generating your research paper. Please wait...' }
    ]);
    
    setShowPaper(false);
  
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
          "References"
        ],
        wordCount: 3000,
        sourceType: inputData.source || null,
        sourceUrl: inputData.url || null
      };
  
      console.log("Sending request data:", JSON.stringify(requestData));
  
      // Make API call to the backend
      const response = await fetch('/api/research/generate-paper', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });
      
      if (!response.ok) {
        console.error("Server response not OK:", response.status, response.statusText);
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
        setChatMessages(prev => [...prev, { 
          role: 'system', 
          text: 'Your paper is being generated. This may take a few minutes.' 
        }]);
        
        // Poll for updates
        pollIntervalRef.current = setInterval(async () => {
          try {
            const statusResponse = await fetch(`/api/research/paper/${documentId}`);
            
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
                setChatMessages(prev => [...prev, { 
                  role: 'system', 
                  text: 'Error: Paper content is empty. Please try again with a different topic or repository.' 
                }]);
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
            setChatMessages(prev => [...prev, { 
              role: 'system', 
              text: `Error: ${pollError.message}. Please try again.` 
            }]);
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
          setChatMessages(prev => [...prev, { 
            role: 'system', 
            text: 'Error: Paper content is empty. Please try again with a different topic or repository.' 
          }]);
          setIsProcessing(false);
          setIsGenerating(false);
        }
      } else {
        throw new Error(data.message || 'Unknown error occurred');
      }
    } catch (error) {
      console.error('Error generating paper:', error);
      clearInterval(stepIntervalRef.current);
      stepIntervalRef.current = null;
      
      setError(error.message);
      setChatMessages(prev => [...prev, { 
        role: 'system', 
        text: `Error: ${error.message}. Please try again.` 
      }]);
      setIsProcessing(false);
      setIsGenerating(false);
    }
  };
  
  // Improved handlePaperGenerated function
  const handlePaperGenerated = (paperText, prompt) => {
    try {
      // Safety check for paperText
      if (!paperText) {
        console.error("Paper text is empty or undefined");
        setChatMessages(prev => [
          ...prev,
          { role: 'system', text: 'Error: Unable to generate paper content.' }
        ]);
        setIsProcessing(false);
        setIsGenerating(false);
        return;
      }
      
      // Set the paper content
      setPaperContent(paperText);
      
      // Generate a synopsis from the abstract section or first paragraph
      const abstractMatch = paperText.match(/Abstract([\s\S]*?)(?=\n##|\n#|$)/i);
      const synopsisText = abstractMatch 
        ? abstractMatch[1].trim() 
        : `This research paper explores ${prompt}, analyzing key aspects and providing insights into this field of study.`;
      
      setSynopsis(synopsisText);
      
      // Create chat messages for each section
      const sectionRegex = /##\s*(.*?)\n([\s\S]*?)(?=\n##|\n#|$)/g;
      const chatMessageArray = [
        { role: 'system', text: 'Paper generation complete. Here are the sections:' }
      ];
      
      let match;
      let sections = [];
      
      while ((match = sectionRegex.exec(paperText)) !== null) {
        const sectionTitle = match[1].trim();
        const sectionContent = match[2].trim();
        
        // Add to sections array for tracking
        sections.push(sectionTitle);
        
        // Add section message to chat
        chatMessageArray.push({
          role: 'assistant',
          text: `## ${sectionTitle}\n${sectionContent.length > 300 ? 
            sectionContent.substring(0, 300) + '...' : 
            sectionContent}`
        });
      }
      
      // If no sections were found, add the whole content as one message
      if (sections.length === 0) {
        chatMessageArray.push({
          role: 'assistant',
          text: paperText.length > 500 ? paperText.substring(0, 500) + '...' : paperText
        });
      }
      
      // Add a summary of sections
      if (sections.length > 0) {
        chatMessageArray.splice(1, 0, { 
          role: 'system', 
          text: `Generated paper contains the following sections: ${sections.join(', ')}` 
        });
      }
      
      // Complete processing and show paper
      setCurrentStep(processingSteps.length - 1);
      
      // Clear step interval if still running
      if (stepIntervalRef.current) {
        clearInterval(stepIntervalRef.current);
        stepIntervalRef.current = null;
      }
      
      // First set initial messages and show paper
      setTimeout(() => {
        setIsProcessing(false);
        setShowPaper(true);
        
        // Keep existing messages and add just first message
        setChatMessages(prev => [...prev, chatMessageArray[0]]);
        
        // Then add remaining messages progressively with a reference for cleanup
        let index = 1;
        messageIntervalRef.current = setInterval(() => {
          if (index < chatMessageArray.length) {
            setChatMessages(prev => [...prev, chatMessageArray[index]]);
            index++;
          } else {
            clearInterval(messageIntervalRef.current);
            messageIntervalRef.current = null;
            setIsGenerating(false);
          }
        }, 1000);
      }, 1500);
    } catch (err) {
      console.error("Error in handlePaperGenerated:", err);
      
      // Clear any running intervals
      if (stepIntervalRef.current) clearInterval(stepIntervalRef.current);
      if (messageIntervalRef.current) clearInterval(messageIntervalRef.current);
      stepIntervalRef.current = null;
      messageIntervalRef.current = null;
      
      setError("An error occurred while processing the generated paper. Please try again.");
      setChatMessages(prev => [...prev, { 
        role: 'system', 
        text: `Error: ${err.message}. Please try again.` 
      }]);
      setIsProcessing(false);
      setIsGenerating(false);
    }
  };

  // Auto scroll to bottom when new message arrives
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages]);

  // Add error boundary effect
  useEffect(() => {
    // This will help recover from rendering errors
    const handleError = (error) => {
      console.error("Caught runtime error:", error);
      
      // Clean up all intervals on error
      if (stepIntervalRef.current) clearInterval(stepIntervalRef.current);
      if (messageIntervalRef.current) clearInterval(messageIntervalRef.current);
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      stepIntervalRef.current = null;
      messageIntervalRef.current = null;
      pollIntervalRef.current = null;
      
      setError("A rendering error occurred. Please refresh the page.");
      setIsProcessing(false);
      setIsGenerating(false);
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  const features = [
    {
      icon: <FileText className="feature-icon" />,
      title: "IEEE Format",
      description: "Automatically generates papers following IEEE formatting guidelines"
    },
    {
      icon: <Sparkles className="feature-icon" />,
      title: "AI-Powered Analysis",
      description: "Advanced AI algorithms analyze your code and generate human-readable content"
    },
    {
      icon: <FileText className="feature-icon" />,
      title: "Research Quality",
      description: "Produces academic-grade content suitable for publication"
    }
  ];

  return (
    <div className={`container ${layoutChanged ? 'layout-changed' : ''}`}>
      <div className="header">
        <div className="logo">
          <FileText className="logo-icon" />
          <span>AI Research Paper Generator</span>
        </div>
        <h1>Transform Your Code into Research Papers</h1>
        <p>
          Generate conference-formatted research papers automatically from your GitHub repositories
          <br />or code projects using advanced AI.
        </p>
      </div>

      <div className={`main-content ${layoutChanged ? 'two-column' : ''}`}>
        {/* Left Column - Chat History and Input */}
        <div className="left-column">
          {layoutChanged && (
            <div className="chat-container-left" ref={chatContainerRef}>
              {isProcessing && (
                <div className="processing-container-left">
                  {processingSteps.map((step, index) => (
                    <div key={index} className={`processing-step ${index === currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}>
                      <div className="processing-icon">{step.icon}</div>
                      <p>{step.text}</p>
                    </div>
                  ))}
                </div>
              )}
              
              {showPaper && synopsis && (
                <div className="chat-message system">
                  <strong>Paper Synopsis:</strong>
                  {synopsis}
                </div>
              )}
              
              {/* This is the part that's causing the error - needs a null check */}
              {chatMessages && chatMessages.length > 0 && chatMessages.map((msg, index) => (
                // Add null check to make sure msg and msg.role exist
                msg && msg.role ? (
                  <div key={`msg-${index}`} className={`chat-message ${msg.role}`}>
                    {msg.text}
                  </div>
                ) : null
              ))}
              
              {error && (
                <div className="chat-message error">
                  {error}
                </div>
              )}
              
              {isGenerating && (
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              )}
            </div>
          )}

          {/* Integrated Input Section */}
          <div className={`input-section-container ${isGenerating ? 'generating' : ''}`}>
            <form onSubmit={handleSubmit} className="input-container">
              {/* Source Selection Button */}
              <button
                type="button"
                onClick={() => setIsSourceMenuOpen(!isSourceMenuOpen)}
                className="source-button"
                disabled={isGenerating}
              >
                <Pin size={20} />
              </button>

              {/* Main Input Field */}
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Message AcademAI..."
                className="input-field"
                rows={1}
                disabled={isGenerating}
              />
              
              <button
                type="submit"
                className="send-button"
                disabled={!inputValue.trim() || isGenerating}
              >
                <Send size={20} />
              </button>

              {/* Source Selection Menu */}
              {isSourceMenuOpen && (
                <div className="source-menu">
                  <button
                    type="button"
                    onClick={() => handleSourceSelect('github')}
                    className="source-option"
                  >
                    <Github size={20} />
                    <span>GitHub Repository</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSourceSelect('folder')}
                    className="source-option"
                  >
                    <Folder size={20} />
                    <span>Upload Folder</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSourceSelect('drive')}
                    className="source-option"
                  >
                    <FileText size={20} />
                    <span>Google Drive</span>
                  </button>
                </div>
              )}
            </form>

            {/* Source URL Input */}
            {selectedSource && (
              <div className="source-input-wrapper">
                {selectedSource === 'github' && (
                  <input
                    type="url"
                    placeholder="Enter GitHub repository URL"
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    className="source-input"
                    disabled={isGenerating}
                  />
                )}
                {selectedSource === 'folder' && (
                  <div>
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileUpload}
                      webkitdirectory="true"
                      multiple
                      style={{ display: 'none' }}
                      disabled={isGenerating}
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="folder-upload-button"
                      disabled={isGenerating}
                    >
                      Choose Folder
                    </button>
                  </div>
                )}
                {selectedSource === 'drive' && (
                  <input
                    type="url"
                    placeholder="Enter Google Drive link"
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    className="source-input"
                    disabled={isGenerating}
                  />
                )}
              </div>
            )}

            {!layoutChanged && (
              <div className="chat-disclaimer">
                AcademAI may display inaccurate info, including about people, places, facts, and events
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Generated Content */}
        {layoutChanged && (
          <div className="right-column">
            {/* Paper Content */}
            {showPaper && (
              <div className="paper-container">
                <h2>Generated Research Paper</h2>
                <p className="paper-subtitle">You can edit the content below:</p>
                <textarea
                  className="paper-content"
                  value={paperContent}
                  onChange={(e) => setPaperContent(e.target.value)}
                  rows={20}
                />
                <div className="paper-actions">
                  <button className="submit-button">Download as PDF</button>
                  <button 
                    className="submit-button secondary"
                    onClick={() => {
                      navigator.clipboard.writeText(paperContent);
                      alert('Paper content copied to clipboard!');
                    }}
                  >
                    Copy to Clipboard
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Features Section - Only visible before layout change */}
      {!layoutChanged && (
        <div className="features-section">
          <h2>Features</h2>
          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className="feature-card">
                <div className="feature-icon-wrapper">
                  {feature.icon}
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResearchPaperGenerator;