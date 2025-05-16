import { useState, useRef, useEffect } from "react";
import {
  FileText,
  Sparkles,
  Brain,
  Code,
  PenTool,
  Bot,
  Github,
  SendHorizontal,
  Edit,
  Copy,
  MessageSquare,
  X,
  FileDown,
  File,
} from "lucide-react";
import { useChatHistory } from "../context/ChatHistoryContext.jsx";
import LeftDrawer from "./LeftDrawer";
import ChatMessage from "./ChatMessage";
import "./ResearchPaperGenerator.css";
import "./ResearchPaperStyles.css";
import "./ChatMessageStyles.css";
import AuthService from "../services/AuthService";
import ActivityService from "../services/ActivityService";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { saveAs } from "file-saver";

// Configure marked with better defaults
marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: true,
});

const ResearchPaperGenerator = () => {
  // Access chat history context
  const {
    addChat,
    updateMessages,
    updateChatTitle,
    getCurrentChat,
    selectedChatId,
    selectChat,
  } = useChatHistory();

  // All state and refs
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [showPaper, setShowPaper] = useState(false);
  const [isEditingPaper, setIsEditingPaper] = useState(false);
  const [paperContent, setPaperContent] = useState("");
  const [paperHtml, setPaperHtml] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [layoutChanged, setLayoutChanged] = useState(false);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(false);
  // Check if user is authenticated
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userData, setUserData] = useState(null);

  // Input Section states
  const [showGithubInput, setShowGithubInput] = useState(false);
  const [selectedSource, setSelectedSource] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const chatContainerRef = useRef(null);
  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);
  const paperContentRef = useRef(null);
  const githubInputRef = useRef(null);

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
    if (!markdown) return "";

    try {
      // Convert markdown to HTML
      const rawHtml = marked.parse(markdown);

      // Sanitize HTML to prevent XSS attacks
      const sanitizedHtml = DOMPurify.sanitize(rawHtml);

      return sanitizedHtml;
    } catch (error) {
      console.error("Error converting markdown to HTML:", error);
      return `<p>Error rendering content: ${error.message}</p>`;
    }
  };

  // Function to handle HTML download
  const handleHtmlDownload = () => {
    try {
      // For HTML saving
      const htmlOutput = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${getCurrentChat()?.topic || "Research Paper"}</title>
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
      saveAs(blob, `research-paper-${Date.now()}.html`);

      // Find paper's document ID if available
      const paperMessage = chatMessages.find(
        (msg) => msg.role === "assistant" && msg.paperContent
      );
      const documentId = paperMessage?.documentId;

      // Track download if user is authenticated
      if (isAuthenticated && userData && documentId) {
        ActivityService.trackPaperDownload(documentId, "html");
      }

      // Create a system message to inform the user
      const systemMessage = {
        role: "system",
        text: "Research paper saved as HTML",
      };
      const newMessages = [...chatMessages, systemMessage];
      setChatMessages(newMessages);
      updateMessages(newMessages);
    } catch (error) {
      console.error("Error saving paper as HTML:", error);
      setError("Failed to save paper: " + error.message);
    }
  };

  // Function to handle DOCX download
  const handleDocxDownload = async () => {
    try {
      // Get the paper title from current chat
      const title = getCurrentChat()?.topic || "Research Paper";

      // Create a full HTML document
      const fullHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>${title}</title>
    <style>
        body { font-family: 'Times New Roman', Times, serif; line-height: 1.6; margin: 1in; }
        h1 { font-size: 16pt; font-weight: bold; margin-top: 12pt; text-align: center; }
        h2 { font-size: 14pt; font-weight: bold; margin-top: 10pt; }
        h3 { font-size: 12pt; font-weight: bold; margin-top: 8pt; }
        p { font-size: 12pt; margin: 6pt 0; }
        blockquote { margin-left: 24pt; font-style: italic; }
        code { font-family: 'Courier New', monospace; }
        .ieee-paper { max-width: 8.5in; }
    </style>
</head>
<body>
    <div class="ieee-paper">
        ${paperHtml}
    </div>
</body>
</html>
      `;

      // Create a blob
      const blob = new Blob([fullHtml], {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      });

      // Save the file
      saveAs(blob, `${title.replace(/[^a-zA-Z0-9]/g, "_")}_${Date.now()}.docx`);

      // Find paper's document ID if available
      const paperMessage = chatMessages.find(
        (msg) => msg.role === "assistant" && msg.paperContent
      );
      const documentId = paperMessage?.documentId;

      // Track download if user is authenticated
      if (isAuthenticated && userData && documentId) {
        ActivityService.trackPaperDownload(documentId, "docx");
      }

      // Create a system message to inform the user
      const systemMessage = {
        role: "system",
        text: "Research paper saved as DOCX",
      };
      const newMessages = [...chatMessages, systemMessage];
      setChatMessages(newMessages);
      updateMessages(newMessages);
    } catch (error) {
      console.error("Error saving paper as DOCX:", error);
      setError("Failed to save paper as DOCX: " + error.message);

      // Try fallback method
      try {
        const title = getCurrentChat()?.topic || "Research Paper";

        // Simple fallback conversion
        const fullHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>${title}</title>
    <style>
        body { font-family: 'Times New Roman', Times, serif; line-height: 1.6; }
        h1 { font-size: 16pt; font-weight: bold; }
        h2 { font-size: 14pt; font-weight: bold; }
        p { font-size: 12pt; }
    </style>
</head>
<body>
    ${paperHtml}
</body>
</html>
        `;

        const blob = new Blob([fullHtml], {
          type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        });
        saveAs(
          blob,
          `${title.replace(/[^a-zA-Z0-9]/g, "_")}_${Date.now()}.docx`
        );

        // Create a system message to inform the user
        const systemMessage = {
          role: "system",
          text: "Research paper saved as DOCX (fallback method)",
        };
        const newMessages = [...chatMessages, systemMessage];
        setChatMessages(newMessages);
        updateMessages(newMessages);
      } catch (fallbackError) {
        console.error("Fallback DOCX conversion failed:", fallbackError);
        setError(
          "All DOCX conversion methods failed. Please try HTML format instead."
        );
      }
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

  // Extract a good chat title from the first user message
  const generateChatTitle = (message) => {
    // Clean up the message text
    const cleanMessage = message
      .replace(/\n/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    // Take up to 50 characters for the title
    const title =
      cleanMessage.substring(0, 50) + (cleanMessage.length > 50 ? "..." : "");

    return title;
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

  // Toggle GitHub URL input field
  const toggleGithubInput = () => {
    // If we're already showing the GitHub input and have the source set, clear it
    if (showGithubInput && selectedSource === "github") {
      setSelectedSource(null);
      setSourceUrl("");
      setShowGithubInput(false);
    } else {
      // Otherwise, show the GitHub input and set github as the source
      setSelectedSource("github");
      setShowGithubInput(true);
      // Focus the input field after it appears
      setTimeout(() => {
        if (githubInputRef.current) {
          githubInputRef.current.focus();
        }
      }, 100);
    }
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

  // Check authentication status on component mount
  useEffect(() => {
    const checkAuth = () => {
      const isAuth = AuthService.isAuthenticated();
      setIsAuthenticated(isAuth);

      if (isAuth) {
        const user = AuthService.getCurrentUser();
        setUserData(user);
      } else {
        setUserData(null);
      }
    };

    checkAuth();

    // Set up auth check interval (for token expiration)
    const authInterval = setInterval(checkAuth, 5 * 60 * 1000); // Check every 5 minutes

    return () => {
      if (authInterval) clearInterval(authInterval);
    };
  }, []);

  // Add the missing handleOpenFullPaper function
  const handleOpenFullPaper = (message) => {
    if (message.paperContent) {
      setPaperContent(message.paperContent);
      setPaperHtml(convertMarkdownToHtml(message.paperContent));
      setShowPaper(true);

      // Track paper view if user is authenticated
      if (isAuthenticated && userData && message.documentId) {
        ActivityService.trackPaperView(message.documentId);
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isGenerating) return;

    if (selectedSource === "github" && !sourceUrl.trim()) {
      alert("Please enter a GitHub repository URL.");
      return;
    }

    const inputData = {
      prompt: inputValue,
      source: selectedSource,
      url: sourceUrl,
      timestamp: new Date().toLocaleTimeString(),
    };

    // Create a new chat if none is selected
    if (!selectedChatId) {
      const chatTopic = generateChatTitle(inputValue);
      const newChatId = addChat(chatTopic);
      selectChat(newChatId);

      // Track new chat creation if user is authenticated
      if (isAuthenticated && userData) {
        ActivityService.trackNewChat(newChatId, chatTopic);
      }
    } else {
      // If this is the first message, update the chat title
      const currentChat = getCurrentChat();
      if (
        currentChat &&
        (!currentChat.messages || currentChat.messages.length === 0)
      ) {
        const chatTopic = generateChatTitle(inputData.prompt);
        if (typeof updateChatTitle === "function") {
          updateChatTitle(selectedChatId, chatTopic);
        } else {
          console.warn("updateChatTitle function is not defined.");
        }
      }
    }

    // Call the API integration function
    handleFormSubmission(inputData);

    // Change to two-column layout
    setLayoutChanged(true);

    // Clear the input
    setInputValue("");
    setSourceUrl("");
    setSelectedSource(null);
    setShowGithubInput(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Handle key down for GitHub URL input
  const handleGithubKeyDown = (e) => {
    if (e.key === "Enter") {
      // Focus back on the main input field
      textareaRef.current?.focus();
    } else if (e.key === "Escape") {
      setShowGithubInput(false);
      setSelectedSource(null);
      setSourceUrl("");
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

      // Add authentication header if user is logged in
      const headers = {
        "Content-Type": "application/json",
      };

      if (isAuthenticated && userData) {
        headers["Authorization"] = `Bearer ${userData.token}`;
      }

      // Make API call to the backend
      const response = await fetch("/api/research/generate-paper", {
        method: "POST",
        headers,
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
                handlePaperGenerated(statusData.paper, documentId);
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
          handlePaperGenerated(data.paper, data.document_id);
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

  const handlePaperGenerated = (paperText, documentId) => {
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
      documentId: documentId,
      timestamp: new Date().toISOString(),
    };

    // Update chat messages by removing the loading message and adding the assistant response
    const newMessages = [
      ...chatMessages.filter((msg) => msg.role !== "system"),
      assistantMessage,
    ];
    setChatMessages(newMessages);
    updateMessages(newMessages);

    // Track paper generation if user is authenticated
    if (isAuthenticated && userData) {
      ActivityService.trackPaperGeneration({
        documentId: documentId,
        topic: getCurrentChat()?.topic || "Untitled Research",
        wordCount: paperText.split(/\s+/).length,
      });
    }

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
                      minHeight: "70vh",
                      padding: "30px",
                      border: "1px solid #ddd",
                      borderRadius: "4px",
                      fontFamily: "'Times New Roman', Times, serif",
                      fontSize: "16px",
                      lineHeight: "1.6",
                      resize: "vertical",
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
                          setPaperHtml(
                            convertMarkdownToHtml(paperMessage.paperContent)
                          );
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

                  {/* New simplified action buttons */}
                  {/* New simplified action buttons */}
                  <div className="paper-actions">
                    <div className="paper-actions-inner">
                      <button
                        className="submit-button secondary"
                        onClick={handleCopyToClipboard}
                      >
                        <Copy size={18} />
                        Copy to Clipboard
                      </button>

                      <button
                        className="submit-button secondary"
                        onClick={handleDocxDownload}
                      >
                        <FileDown size={18} />
                        Download as DOCX
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ) : (
            // fallback to chat UI if no paper
            <>
              <div
                className="chat-container"
                ref={chatContainerRef}
                style={{ display: chatMessages.length > 0 ? "flex" : "none" }}
              >
                {chatMessages.map((message, index) => (
                  <ChatMessage key={index} message={message} />
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
                      Enter your topic or provide a code repository to generate
                      a research paper
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
              <div className="input-form-container">
                <div className="input-container">
                  {selectedSource === "github" && !showGithubInput && (
                    <div className="active-source">
                      <Github size={18} />
                      <span>{sourceUrl || "GitHub Repository"}</span>
                      <button
                        type="button"
                        className="remove-source"
                        onClick={() => {
                          setSelectedSource(null);
                          setSourceUrl("");
                        }}
                      >
                        <X size={14} />
                      </button>
                    </div>
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
                    className={`source-button ${
                      selectedSource === "github" ? "active" : ""
                    }`}
                    onClick={toggleGithubInput}
                    title="Add GitHub repository"
                  >
                    <Github size={18} />
                  </button>

                  <button
                    type="submit"
                    className="send-button"
                    disabled={!inputValue.trim() || isGenerating}
                  >
                    <SendHorizontal size={18} />
                  </button>
                </div>

                {/* GitHub URL input field appears directly below the main input */}
                {showGithubInput && (
                  <div className="github-url-container">
                    <div className="github-url-input-wrapper">
                      <Github size={18} className="github-input-icon" />
                      <input
                        ref={githubInputRef}
                        type="text"
                        value={sourceUrl}
                        onChange={(e) => setSourceUrl(e.target.value)}
                        onKeyDown={handleGithubKeyDown}
                        placeholder="Enter GitHub repository URL..."
                        className="github-url-input"
                      />
                      <button
                        type="button"
                        className="github-url-close"
                        onClick={() => {
                          setShowGithubInput(false);
                          if (!sourceUrl.trim()) {
                            setSelectedSource(null);
                          }
                        }}
                      >
                        <X size={14} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearchPaperGenerator;
