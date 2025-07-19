// src/components/LandingPage.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInView } from 'react-intersection-observer';
import { motion } from 'framer-motion';
import { GoogleLogin } from '@react-oauth/google';
import { FileText, Code, Lock, Zap, Globe, UserCheck } from 'lucide-react';
import AuthService from '../services/AuthService';
import './LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState(null);
  
  const { ref, inView } = useInView({
    threshold: 0.1,
    triggerOnce: true,
  });

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      setIsLoggingIn(true);
      setLoginError(null);
      
      // Process Google login via our AuthService
      await AuthService.handleGoogleLogin(credentialResponse);
      
      // Navigate to generator page on success
      navigate('/generator');
    } catch (error) {
      console.error('Google Auth Error:', error);
      setLoginError('Login failed. Please try again.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleGoogleError = () => {
    console.error('Google Auth Error');
    setLoginError('Failed to connect with Google. Please try again later.');
  };

  const features = [
    { icon: <FileText />, title: 'IEEE Format', description: 'Automatically formatted papers following strict IEEE guidelines' },
    { icon: <Code />, title: 'Code Analysis', description: 'Deep analysis of your codebase with advanced AI algorithms' },
    { icon: <Lock />, title: 'Secure', description: 'Your code and data are encrypted and never stored' },
    { icon: <Zap />, title: 'Lightning Fast', description: 'Get your research paper in minutes, not hours' },
    { icon: <Globe />, title: 'Multiple Languages', description: 'Support for all major programming languages' },
    { icon: <UserCheck />, title: 'Easy to Use', description: 'Simple interface with powerful capabilities' }
  ];

  return (
    <div className="landing-container">
      {/* Hero Section */}
      <motion.section 
        className="hero-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <nav className="navbar">
          <div className="logo">
            <FileText />
            <span>AcademAI</span>
          </div>
        </nav>

        <div className="hero-content">
          <motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.8 }}>
            Transform Your Code into <span className="gradient-text"> Research Papers</span>
          </motion.h1>
          <motion.p initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4, duration: 0.8 }}>
            Use AI to automatically generate IEEE-formatted research papers from your code. Save hours of work and focus on what matters most.
          </motion.p>
          <motion.div className="hero-buttons" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6, duration: 0.8 }}>
            {loginError && (
              <div className="login-error">{loginError}</div>
            )}
            
            {!isLoggingIn ? (
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                useOneTap
                theme="filled_blue"
                size="large"
                text="signin_with"
                shape="rectangular"
              />
            ) : (
              <div className="login-loader">
                <div className="spinner"></div>
                <span>Connecting to your account...</span>
              </div>
            )}
          </motion.div>
        </div>

        <motion.div className="hero-image" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.8, duration: 0.8 }}>
          <div className="code-window">
            <div className="code-header">
              <div className="code-dots">
                <span></span><span></span><span></span>
              </div>
              <span>main.py</span>
            </div>
            <pre>
              <code>
                {`def analyze_code():
  # AI-powered analysis
  results = ai_model.process(
      repository.get_contents()
  )
  
  return generate_paper(results)`}
              </code>
            </pre>
          </div>
        </motion.div>
      </motion.section>

      {/* Features Section */}
      <section className="features-section" ref={ref}>
        <motion.h2 initial={{ opacity: 0, y: 30 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.8 }}>
          Powerful Features
        </motion.h2>
        <div className="features-grid">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              className="feature-card"
              initial={{ opacity: 0, y: 30 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: index * 0.1, duration: 0.8 }}
            >
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Call to Action */}
      <motion.section 
        className="cta-section"
        initial={{ opacity: 0, y: 30 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.8 }}
      >
        <h2>Ready to Generate Your Research Paper?</h2>
        <p>Join thousands of researchers who save time with AI-powered paper generation.</p>
      </motion.section>
    </div>
  );
};

export default LandingPage;