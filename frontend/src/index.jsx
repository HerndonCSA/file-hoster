import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.scss';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
const API_URL = "https://drive-api.soos.dev"

// Create a dark theme instance
const darkTheme = createTheme({
    palette: {
        mode: 'dark',
    },
});

function Root() {
    const [password, setPassword] = useState('');
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(false);
    const [buttonText, setButtonText] = useState('Enter');
    const [buttonClass, setButtonClass] = useState('passwordButton');

    const handlePasswordChange = (event) => {
        setPassword(event.target.value);
    };

    const handleKeyPress = (event) => {
        if (event.key === 'Enter' && !loading) {
            verifyPassword();
        }
    };

    const verifyPassword = () => {
        setLoading(true);
        setButtonText('Verifying...');  // Change button text to indicate loading
        fetch(API_URL, {
          method: 'GET',
          headers: {
            'Authorization': password,
          },
        })
        .then(response => {
          if (response.ok || response.status !== 403) { // Assuming 'ok' or any status other than 403 means success
            setIsAuthenticated(true);
            setButtonText('Enter');
          } else {
            throw new Error('Forbidden'); // Handle specifically 403 Forbidden
          }
        })
        .catch(error => {
          if (error.message === 'Forbidden') {
            // Specific action for 403
            setButtonClass('passwordButton incorrect');
            setButtonText('Incorrect');
          } else {
            // General network error or CORS issue, treat as incorrect password for simplicity
            setButtonClass('passwordButton incorrect');
            setButtonText('Incorrect');
          }
        })
        .finally(() => {
          setTimeout(() => {
            setButtonClass('passwordButton');
            setButtonText('Enter');
            setLoading(false);
          }, 5000);
        });
      };
      

    return (
        <ThemeProvider theme={darkTheme}>
            <div className="login-container">
                {isAuthenticated ? (
                    <App key={password} />
                ) : (
                    <div className="login-form">
                        <TextField
                            label="Password"
                            type="password"
                            variant="outlined"
                            value={password}
                            onChange={handlePasswordChange}
                            onKeyPress={handleKeyPress}
                            fullWidth
                            disabled={loading}
                        />
                        <Button
                            variant="contained"
                            color="primary"
                            onClick={verifyPassword}
                            className={buttonClass}
                            disabled={loading}
                        >
                            {buttonText}
                        </Button>
                    </div>
                )}
            </div>
        </ThemeProvider>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<Root />);
