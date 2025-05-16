// src/services/AuthService.js
import { jwtDecode } from 'jwt-decode';

class AuthService {
  // Process Google OAuth login response
  handleGoogleLogin = async (credentialResponse) => {
    try {
      const token = credentialResponse.credential;
      const decodedToken = jwtDecode(token);
      
      // Create user data object
      const userData = {
        googleId: decodedToken.sub,
        name: decodedToken.name,
        email: decodedToken.email,
        avatar: decodedToken.picture,
        token: token,
        lastLogin: new Date().toISOString()
      };
      
      // Store token and user data in localStorage
      localStorage.setItem('userToken', token);
      localStorage.setItem('userData', JSON.stringify(userData));
      
      // Call API to register/login the user
      await this.saveUserToDatabase(userData);
      
      return userData;
    } catch (error) {
      console.error('Error handling Google login:', error);
      throw error;
    }
  };
  
  // Send user data to backend for database storage
  saveUserToDatabase = async (userData) => {
    try {
      const response = await fetch('/api/auth/google-signin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });
      
      if (!response.ok) {
        throw new Error('Failed to save user data');
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error saving user to database:', error);
      // Still proceed even if server storage fails
      // This ensures the user can use the app even if the backend has issues
    }
  };
  
  // Check if user is logged in
  isAuthenticated = () => {
    const token = localStorage.getItem('userToken');
    if (!token) return false;
    
    try {
      // Check if token is expired
      const decodedToken = jwtDecode(token);
      const currentTime = Date.now() / 1000;
      return decodedToken.exp > currentTime;
    } catch (error) {
      return false;
    }
  };
  
  // Get current user data
  getCurrentUser = () => {
    try {
      const userData = localStorage.getItem('userData');
      return userData ? JSON.parse(userData) : null;
    } catch {
      return null;
    }
  };
  
  // Logout user
  logout = async () => {
    try {
      // Call logout API to update user's session data in database
      const userData = this.getCurrentUser();
      if (userData) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${userData.token}`
          },
          body: JSON.stringify({ userId: userData.googleId })
        }).catch(err => console.error('Error logging out on server:', err));
      }
    } finally {
      // Always clear local storage regardless of server response
      localStorage.removeItem('userToken');
      localStorage.removeItem('userData');
    }
  };
}

export default new AuthService();