// src/services/ActivityService.js
import AuthService from './AuthService';

class ActivityService {
  constructor() {
    this.sessionId = null;
    this.queuedActivities = [];
    this.processInterval = null;
    
    // Start processing queue every 10 seconds
    this.processInterval = setInterval(() => this.processQueue(), 10000);
  }
  
  // Track user activity
  trackActivity = async (activityType, activityDetails = {}) => {
    try {
      const user = AuthService.getCurrentUser();
      if (!user) return; // Don't track if not logged in
      
      const activity = {
        type: activityType,
        details: activityDetails,
        timestamp: new Date().toISOString(),
        sessionId: this.sessionId
      };
      
      // Add to queue for batch processing
      this.queuedActivities.push(activity);
      
      // If queue is getting long, process immediately
      if (this.queuedActivities.length >= 5) {
        this.processQueue();
      }
    } catch (error) {
      console.error('Error tracking activity:', error);
    }
  };
  
  // Track when user generates a paper
  trackPaperGeneration = async (paperDetails) => {
    return this.trackActivity('paper_generation', {
      topic: paperDetails.topic,
      sections: paperDetails.sections,
      wordCount: paperDetails.wordCount,
      sourceType: paperDetails.sourceType,
      sourceUrl: paperDetails.sourceUrl,
      documentId: paperDetails.documentId
    });
  };
  
  // Track when user views a paper
  trackPaperView = async (documentId) => {
    return this.trackActivity('paper_view', { documentId });
  };
  
  // Track when user edits a paper
  trackPaperEdit = async (documentId) => {
    return this.trackActivity('paper_edit', { documentId });
  };
  
  // Track when user downloads a paper
  trackPaperDownload = async (documentId, format) => {
    return this.trackActivity('paper_download', { documentId, format });
  };
  
  // Track when user creates a new chat
  trackNewChat = async (chatId, topic) => {
    return this.trackActivity('new_chat', { chatId, topic });
  };
  
  // Track when user deletes a chat
  trackDeleteChat = async (chatId) => {
    return this.trackActivity('delete_chat', { chatId });
  };
  
  // Process queued activities
  processQueue = async () => {
    if (this.queuedActivities.length === 0) return;
    
    const activities = [...this.queuedActivities];
    this.queuedActivities = [];
    
    try {
      const user = AuthService.getCurrentUser();
      if (!user) return;
      
      await fetch('/api/auth/track-activity', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({ activities })
      });
    } catch (error) {
      console.error('Error sending activities to server:', error);
      // Add back to queue to try again later
      this.queuedActivities = [...activities, ...this.queuedActivities];
    }
  };
  
  // Clean up when service is destroyed
  cleanup = () => {
    if (this.processInterval) {
      clearInterval(this.processInterval);
      this.processInterval = null;
    }
    
    // Process any remaining activities
    if (this.queuedActivities.length > 0) {
      this.processQueue();
    }
  };
}

export default new ActivityService();