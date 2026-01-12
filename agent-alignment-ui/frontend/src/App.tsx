import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import EvaluationPage from './pages/EvaluationPage';
import HITLPage from './pages/HITLPage';
import HistoryPage from './pages/HistoryPage';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Create custom theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 8,
        },
      },
    },
  },
});

// Add custom alignment colors to theme
declare module '@mui/material/styles' {
  interface Palette {
    alignment: {
      full: string;
      soft: string;
      hard: string;
      insufficient: string;
    };
  }

  interface PaletteOptions {
    alignment?: {
      full?: string;
      soft?: string;
      hard?: string;
      insufficient?: string;
    };
  }
}

const customTheme = createTheme({
  ...theme,
  palette: {
    ...theme.palette,
    alignment: {
      full: '#4caf50',
      soft: '#ff9800',
      hard: '#f44336',
      insufficient: '#9e9e9e',
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={customTheme}>
        <CssBaseline />
        <Router>
          <Box sx={{ display: 'flex', minHeight: '100vh' }}>
            <Sidebar />
            <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
              <Header />
              <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/evaluate" element={<EvaluationPage />} />
                  <Route path="/hitl" element={<HITLPage />} />
                  <Route path="/history" element={<HistoryPage />} />
                </Routes>
              </Box>
            </Box>
          </Box>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;