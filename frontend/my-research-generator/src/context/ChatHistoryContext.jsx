// src/context/ChatHistoryContext.jsx
import { createContext, useContext, useReducer, useEffect } from 'react';
import PropTypes from 'prop-types';
import AuthService from '../services/AuthService';
import ActivityService from '../services/ActivityService';

// Action types
const ADD_CHAT = 'ADD_CHAT';
const SELECT_CHAT = 'SELECT_CHAT';
const UPDATE_MESSAGES = 'UPDATE_MESSAGES';
const DELETE_CHAT = 'DELETE_CHAT';
const SET_CHATS = 'SET_CHATS';
const UPDATE_CHAT_TITLE = 'UPDATE_CHAT_TITLE';
const RESET_STATE = 'RESET_STATE';

const initialState = {
  chats: [],
  selectedChatId: null
};

function chatReducer(state, action) {
  switch (action.type) {
    case ADD_CHAT:
      return {
        ...state,
        chats: [...state.chats, action.payload],
        selectedChatId: action.payload.id
      };
    case SELECT_CHAT:
      return {
        ...state,
        selectedChatId: action.payload
      };
    case UPDATE_MESSAGES: {
      // Extract the first message from user to set as chat title if it's not set yet
      const messages = action.payload;
      const updatedChats = state.chats.map(chat => {
        if (chat.id === state.selectedChatId) {
          // Find first user message for title if not already set
          let updatedChat = { ...chat, messages };
          
          // If this is the first message and no topic is set, extract topic from user message
          if (messages.length > 0 && (!chat.topic || chat.topic === "New Chat")) {
            const firstUserMessage = messages.find(msg => msg.role === 'user');
            if (firstUserMessage) {
              const cleanMessage = firstUserMessage.text
                .replace(/\n/g, ' ')
                .replace(/\s+/g, ' ')
                .trim();
              updatedChat.topic = cleanMessage.substring(0, 50) + (cleanMessage.length > 50 ? "..." : "");
            }
          }
          
          return updatedChat;
        }
        return chat;
      });
      
      return {
        ...state,
        chats: updatedChats
      };
    }
    case UPDATE_CHAT_TITLE:
      return {
        ...state,
        chats: state.chats.map(chat => 
          chat.id === action.payload.chatId
            ? { ...chat, topic: action.payload.title }
            : chat
        )
      };
    case DELETE_CHAT: {
      const remainingChats = state.chats.filter(chat => chat.id !== action.payload);
      return {
        ...state,
        chats: remainingChats,
        selectedChatId: state.selectedChatId === action.payload 
          ? (remainingChats.length > 0 ? remainingChats[0].id : null)
          : state.selectedChatId
      };
    }
    case SET_CHATS:
      return {
        ...state,
        chats: action.payload,
        selectedChatId: action.payload.length > 0 
          ? (state.selectedChatId || action.payload[0].id) 
          : null
      };
    case RESET_STATE:
      return initialState;
    default:
      return state;
  }
}

const ChatHistoryContext = createContext();

export function ChatHistoryProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState, () => {
    try {
      // Get the current user
      const user = AuthService.getCurrentUser();
      
      // If no user is logged in, use the initial state
      if (!user) {
        return initialState;
      }
      
      // Attempt to load chats from localStorage with user-specific key
      const savedState = localStorage.getItem(`chatHistory-${user.googleId}`);
      return savedState ? JSON.parse(savedState) : initialState;
    } catch (error) {
      console.error('Error initializing chat history state:', error);
      return initialState;
    }
  });

  // Save to localStorage whenever state changes
  useEffect(() => {
    try {
      const user = AuthService.getCurrentUser();
      if (user) {
        localStorage.setItem(`chatHistory-${user.googleId}`, JSON.stringify(state));
        
        // Sync with server
        syncChatsWithServer(state.chats);
      }
    } catch (error) {
      console.error('Error saving chat history state:', error);
    }
  }, [state]);
  
  // Load user chats from server when user logs in
  useEffect(() => {
    const loadUserChatsFromServer = async () => {
      try {
        const user = AuthService.getCurrentUser();
        if (!user) return;
        
        const response = await fetch('/api/chats', {
          headers: {
            'Authorization': `Bearer ${user.token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.chats && Array.isArray(data.chats)) {
            dispatch({ type: SET_CHATS, payload: data.chats });
          }
        }
      } catch (error) {
        console.error('Error loading chats from server:', error);
        // If server load fails, continue with local storage
      }
    };
    
    loadUserChatsFromServer();
  }, []);
  
  // Sync chats with server
  const syncChatsWithServer = async (chats) => {
    try {
      const user = AuthService.getCurrentUser();
      if (!user) return;
      
      // Only send if user is authenticated
      await fetch('/api/chats/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({ chats })
      });
    } catch (error) {
      console.error('Error syncing chats with server:', error);
      // Continue even if sync fails
    }
  };

  // Add a new chat
  const addChat = (topic = "New Chat") => {
    const user = AuthService.getCurrentUser();
    const newChat = {
      id: Date.now().toString(),
      topic,
      createdAt: new Date().toISOString(),
      messages: [],
      userId: user ? user.googleId : null
    };
    
    dispatch({ type: ADD_CHAT, payload: newChat });
    
    // Track activity
    ActivityService.trackNewChat(newChat.id, topic);
    
    return newChat.id;
  };

  // Select a chat
  const selectChat = (chatId) => {
    dispatch({ type: SELECT_CHAT, payload: chatId });
  };

  // Update messages in current chat
  const updateMessages = (messages) => {
    dispatch({ type: UPDATE_MESSAGES, payload: messages });
  };

  // Update chat title
  const updateChatTitle = (chatId, title) => {
    dispatch({ 
      type: UPDATE_CHAT_TITLE, 
      payload: { chatId, title } 
    });
  };

  // Delete a chat
  const deleteChat = (chatId) => {
    // Track activity before deleting
    ActivityService.trackDeleteChat(chatId);
    
    dispatch({ type: DELETE_CHAT, payload: chatId });
  };

  // Reset state (for logout)
  const resetState = () => {
    dispatch({ type: RESET_STATE });
  };

  // Get current chat
  const getCurrentChat = () => {
    return state.chats.find(chat => chat.id === state.selectedChatId) || null;
  };

  return (
    <ChatHistoryContext.Provider
      value={{
        chats: state.chats,
        selectedChatId: state.selectedChatId,
        addChat,
        selectChat,
        updateMessages,
        updateChatTitle,
        deleteChat,
        resetState,
        getCurrentChat
      }}
    >
      {children}
    </ChatHistoryContext.Provider>
  );
}

export function useChatHistory() {
  const context = useContext(ChatHistoryContext);
  if (!context) {
    throw new Error('useChatHistory must be used within a ChatHistoryProvider');
  }
  return context;
}

ChatHistoryProvider.propTypes = {
  children: PropTypes.node.isRequired,
};