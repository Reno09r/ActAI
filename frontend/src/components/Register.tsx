import React, { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // Make sure this path is correct

const Register: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); // Clear previous errors

    // Client-side password length validation
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setLoading(true);

    try {
      // --- 1. Registration Attempt ---
      const registerResponse = await fetch('/api/auth/register', { // Ensure this path matches your FastAPI router prefix
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
      });

      // Try to parse JSON. If registerResponse is not .ok and body is not JSON, this will throw.
      // FastAPI error responses (HTTPException) should be JSON.
      const registerData = await registerResponse.json();

      if (!registerResponse.ok) {
        // Registration itself failed. Show error on this page.
        setError(registerData.detail || `Registration failed with status: ${registerResponse.status}`);
        return; // Stop further execution. setLoading will be handled by finally.
      }

      // --- Registration Successful. ---
      // Now, attempt auto-login and user fetch in an inner try-catch.
      // This allows specific error handling for steps after successful registration.
      try {
        // --- 2. Auto-Login Attempt ---
        const loginResponse = await fetch('/api/auth/login', { // Ensure this path is correct
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          // Use username or email for login based on your login endpoint requirements
          body: JSON.stringify({ username: email, password }), // Often email is used as username for login
        });

        const loginData = await loginResponse.json();

        if (!loginResponse.ok) {
          // Auto-login FAILED after successful registration.
          // Redirect to login page with a message.
          console.warn('Auto-login failed after successful registration:', loginData.detail || `Status: ${loginResponse.status}`);
          navigate('/login', { state: { message: "Registration successful! Please log in to continue." } });
          return; // Stop further execution. setLoading will be handled by finally.
        }

        // --- Auto-Login Successful. ---
        // --- 3. Fetch User Details ---
        const userResponse = await fetch('/api/users/me', { // Ensure this path is correct
          headers: {
            'Authorization': `Bearer ${loginData.access_token}`,
          },
        });

        const userData = await userResponse.json();

        if (!userResponse.ok) {
          // Fetching user details FAILED after successful login.
          // User has a token, but we couldn't get their details.
          // Show error on this page (Register page). They might need to log in manually.
          setError(userData.detail || 'Logged in, but failed to fetch user details. Please try logging in again.');
          return; // Stop further execution. setLoading will be handled by finally.
        }

        // --- All Steps Successful ---
        login(loginData.access_token, userData);
        navigate('/dashboard');

      } catch (autoLoginOrUserFetchError) {
        // This inner catch handles network errors or .json() parsing errors
        // specifically for the auto-login or user fetch steps (which occur after successful registration).
        console.error("Error during auto-login or user fetch (after successful registration):", autoLoginOrUserFetchError);
        
        let message = "Registration successful! An error occurred during the auto-login process. Please log in manually.";
        if (autoLoginOrUserFetchError instanceof Error && autoLoginOrUserFetchError.message) {
            // Provide a more specific message if available
             message = `Registration successful! Please log in manually. (Error: ${autoLoginOrUserFetchError.message})`;
        }
        // Since registration was successful, but a subsequent step failed, direct to login page.
        navigate('/login', { state: { message } });
        // No setError needed here as we are navigating away.
        return; // Stop further execution. setLoading will be handled by finally.
      }

    } catch (registrationError) {
      // This outer catch handles errors from the initial registration step:
      // - Network error during the '/api/auth/register' fetch.
      // - Failure to parse JSON from the registration response (e.g., if server sent HTML on a 500 error).
      console.error("Registration step error (network or JSON parse):", registrationError);
      if (registrationError instanceof Error) {
        setError(registrationError.message);
      } else {
        setError('An unexpected error occurred during registration.');
      }
      // setLoading will be handled by finally.
    } finally {
      setLoading(false); // This will always run, ensuring loading state is reset.
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-white to-blue-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8">
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center text-blue-500 hover:text-blue-600"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back
          </button>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-lg">
          <h2 className="text-3xl font-bold mb-6 text-gray-800">Create your account</h2>
          <p className="text-gray-600 mb-8">Start your journey with ActAI today</p>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded break-words">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="space-y-6">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                  Username
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Choose a username"
                  required
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your email"
                  required
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  Password (min. 8 characters)
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Create a password"
                  required
                  minLength={8}
                  disabled={loading}
                />
              </div>

              <button
                type="submit"
                className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading ? 'Creating account...' : 'Create Account'}
              </button>
            </div>
          </form>

          <p className="mt-6 text-center text-gray-600">
            Already have an account?{' '}
            <button
              onClick={() => navigate('/login')}
              className="text-blue-500 hover:text-blue-600 font-medium"
            >
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;