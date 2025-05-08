// src/components/LeftDrawer.jsx
import { useState, useEffect } from 'react';
import { useChatHistory } from '../context/ChatHistoryContext';
import { 
  FileText, 
  MessageSquare, 
  ChevronLeft, 
  ChevronRight, 
  LogOut, 
  PlusCircle, 
  Trash2, 
  Moon, 
  Sun,
  User
} from 'lucide-react';
import './LeftDrawer.css';
import PropTypes from 'prop-types';
import AuthService from '../services/AuthService';
import ActivityService from '../services/ActivityService';

const LeftDrawer = ({ darkMode, toggleDarkMode }) => {
  const [isOpen, setIsOpen] = useState(true);
  const { chats, selectedChatId, selectChat, addChat, deleteChat } = useChatHistory();
  const [userData, setUserData] = useState(null);
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(null);

  // Load user data on component mount
  useEffect(() => {
    const loadUserData = () => {
      // Check if user is authenticated
      if (AuthService.isAuthenticated()) {
        const user = AuthService.getCurrentUser();
        setUserData(user);
      } else {
        setUserData(null);
      }
    };
    
    loadUserData();
    
    // Set up an interval to check authentication status
    const authInterval = setInterval(loadUserData, 5 * 60 * 1000); // Check every 5 minutes
    
    return () => {
      if (authInterval) clearInterval(authInterval);
    };
  }, []);

  const toggleDrawer = () => {
    setIsOpen(!isOpen);
  };

  const handleSelectChat = (chatId) => {
    selectChat(chatId);
    
    // Track chat selection if user is authenticated
    if (userData) {
      ActivityService.trackActivity('select_chat', { chatId });
    }
  };

  const handleNewChat = () => {
    // Reset any pending delete confirmation
    setIsConfirmingDelete(null);
    
    // Create a new chat with a default title
    const newChatId = addChat("New Chat");
    selectChat(newChatId);
    
    // Track new chat creation if user is authenticated
    if (userData) {
      ActivityService.trackNewChat(newChatId, "New Chat");
    }
    
    // Force a complete state reset to ensure new chat is fresh
    setTimeout(() => {
      // This will trigger the useEffect in ResearchPaperGenerator that resets the state
      selectChat(newChatId);
    }, 0);
  };

  const handleDeleteChat = (e, chatId) => {
    e.stopPropagation(); // Prevent triggering chat selection
    
    // If we're already confirming for this chat, proceed with deletion
    if (isConfirmingDelete === chatId) {
      // Delete the chat
      deleteChat(chatId);
      
      // Track chat deletion if user is authenticated
      if (userData) {
        ActivityService.trackDeleteChat(chatId);
      }
      
      // Reset confirmation state
      setIsConfirmingDelete(null);
    } else {
      // Set this chat for confirmation
      setIsConfirmingDelete(chatId);
      
      // Auto-reset after 3 seconds if no action
      setTimeout(() => {
        setIsConfirmingDelete(prev => prev === chatId ? null : prev);
      }, 3000);
    }
  };

  const handleLogout = async () => {
    try {
      // Use AuthService to handle logout properly
      await AuthService.logout();
      
      // Reset user data state
      setUserData(null);
      
      // Force page reload to reset application state
      window.location.reload();
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className={`left-drawer ${isOpen ? '' : 'closed'}`}>
      <div className="drawer-header">
        {isOpen ? (
          <div className="logo">
            <FileText className="logo-icon" />
            <span>ResearchAI</span>
          </div>
        ) : (
          <div className="chat-icon-only">
            <FileText size={24} />
          </div>
        )}
        <button className="toggle-button" onClick={toggleDrawer}>
          {isOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
        </button>
      </div>

      <div className="drawer-content">
        <button className="new-chat-button" onClick={handleNewChat}>
          {isOpen ? (
            <>
              <PlusCircle size={16} />
              <span>New Chat</span>
            </>
          ) : (
            <PlusCircle size={20} />
          )}
        </button>

        {isOpen && (
          <div className="section-header">
            <MessageSquare size={14} />
            <span>Chat History</span>
          </div>
        )}

        <div className="chat-history">
          {chats.length > 0 ? (
            chats.map((chat) => (
              <div
                key={chat.id}
                className={`chat-item ${selectedChatId === chat.id ? 'active' : ''}`}
                onClick={() => handleSelectChat(chat.id)}
              >
                {isOpen ? (
                  <>
                    <div className="chat-item-content">
                      <div className="chat-title">{chat.topic || "Untitled Chat"}</div>
                      <div className="chat-date">{formatDate(chat.createdAt)}</div>
                    </div>
                    <button 
                      className={`delete-chat-button ${isConfirmingDelete === chat.id ? 'confirming' : ''}`}
                      onClick={(e) => handleDeleteChat(e, chat.id)}
                    >
                      {isConfirmingDelete === chat.id ? (
                        <span className="confirm-text">Confirm?</span>
                      ) : (
                        <Trash2 size={16} />
                      )}
                    </button>
                  </>
                ) : (
                  <div className="chat-icon-only">
                    <MessageSquare size={18} />
                  </div>
                )}
              </div>
            ))
          ) : (
            isOpen && <div className="no-chats">No chat history</div>
          )}
        </div>
        
        {isOpen && (
          <button className="theme-toggle-button" onClick={toggleDarkMode}>
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
            <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
        )}
      </div>

      <div className="drawer-footer">
        {userData ? (
          <div className="user-profile">
            {isOpen ? (
              <>
                <img
                  src={userData.avatar || '/default-avatar.png'}
                  alt="User avatar"
                  className="user-avatar"
                />
                <div className="user-info">
                  <div className="user-name">{userData.name || 'User'}</div>
                  <div className="user-email">{userData.email || ''}</div>
                </div>
                <button className="logout-button" onClick={handleLogout}>
                  <LogOut size={18} />
                </button>
              </>
            ) : (
              <div className="user-icon-only">
                <img
                  src={userData.avatar || '/default-avatar.png'}
                  alt="User avatar"
                  className="user-avatar-small"
                />
              </div>
            )}
          </div>
        ) : (
          isOpen ? (
            <div className="login-prompt">
              Sign in to save your chats
            </div>
          ) : (
            <div className="user-icon-only">
              <User size={20} />
            </div>
          )
        )}
      </div>
    </div>
  );
};

LeftDrawer.propTypes = {
  darkMode: PropTypes.bool.isRequired,
  toggleDarkMode: PropTypes.func.isRequired
};

export default LeftDrawer;