import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null); // Pure in-memory storage
  const [loading, setLoading] = useState(true);

  // Attempt to refresh the token on application load
  useEffect(() => {
    const refreshToken = async () => {
      try {
        const response = await api.post('/auth/refresh');
        const { access_token } = response.data;
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        setToken(access_token);
        setUser({ username: 'Admin' }); 
      } catch (error) {
        delete api.defaults.headers.common['Authorization'];
        console.log('No valid session found. User must log in.');
      } finally {
        setLoading(false);
      }
    };

    refreshToken();
  }, []);

  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login', { username, password });
      const { access_token } = response.data;
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setToken(access_token);
      setUser({ username }); 
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (err) {
      console.error('Logout error', err);
    } finally {
      setToken(null);
      setUser(null);
    }
  };

  // Axios Response Interceptor for handling expired tokens
  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // If error is 401 and it's not a retry for the refresh endpoint itself
        if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== '/auth/refresh') {
          originalRequest._retry = true;

          try {
            // Attempt to refresh token
            const refreshResponse = await api.post('/auth/refresh');
            const { access_token } = refreshResponse.data;
            
            // Update token state and defaults
            setToken(access_token);
            api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
            
            // Update the original request with the new token and retry
            originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
            return api(originalRequest);
          } catch (refreshError) {
            // If refresh fails, user must log in again
            setToken(null);
            setUser(null);
            delete api.defaults.headers.common['Authorization'];
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );

    return () => {
      api.interceptors.response.eject(interceptor);
    };
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
