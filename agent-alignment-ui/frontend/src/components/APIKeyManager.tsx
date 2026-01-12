import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Alert,
  IconButton,
  InputAdornment,
  Tabs,
  Tab,
  Link,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Key as KeyIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';

interface APIKeyStatus {
  openai_configured: boolean;
  anthropic_configured: boolean;
  openai_key_preview?: string;
  anthropic_key_preview?: string;
}

interface APIKeyManagerProps {
  open: boolean;
  onClose: () => void;
}

const APIKeyManager: React.FC<APIKeyManagerProps> = ({ open, onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [openaiKey, setOpenaiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [showAnthropicKey, setShowAnthropicKey] = useState(false);

  const queryClient = useQueryClient();

  // Fetch current API key status
  const { data: keyStatus, isLoading } = useQuery({
    queryKey: ['api-keys'],
    queryFn: async (): Promise<APIKeyStatus> => {
      const response = await fetch('/api/config/keys');
      if (!response.ok) {
        throw new Error('Failed to fetch API key status');
      }
      return response.json();
    },
    enabled: open,
  });

  // Update API keys mutation
  const updateKeysMutation = useMutation({
    mutationFn: async (keys: { openai_api_key?: string; anthropic_api_key?: string }) => {
      const response = await fetch('/api/config/keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(keys),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update API keys');
      }
      
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      setOpenaiKey('');
      setAnthropicKey('');
    },
  });

  const handleSaveOpenAI = () => {
    updateKeysMutation.mutate({ openai_api_key: openaiKey });
  };

  const handleSaveAnthropic = () => {
    updateKeysMutation.mutate({ anthropic_api_key: anthropicKey });
  };

  const handleClearOpenAI = () => {
    updateKeysMutation.mutate({ openai_api_key: '' });
  };

  const handleClearAnthropic = () => {
    updateKeysMutation.mutate({ anthropic_api_key: '' });
  };

  const renderKeyStatus = (configured: boolean, preview?: string) => {
    if (configured && preview) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckCircleIcon color="success" />
          <Typography variant="body2" color="success.main">
            Configured: {preview}
          </Typography>
        </Box>
      );
    } else {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ErrorIcon color="error" />
          <Typography variant="body2" color="error">
            Not configured
          </Typography>
        </Box>
      );
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <KeyIcon />
          API Key Configuration
        </Box>
      </DialogTitle>

      <DialogContent>
        <Alert severity="info" sx={{ mb: 3 }}>
          Configure your API keys to enable LLM-powered evaluations. Keys are stored securely and only used for your evaluations.
        </Alert>

        <Tabs value={activeTab} onChange={(_, newValue: number) => setActiveTab(newValue)} sx={{ mb: 3 }}>
          <Tab label="OpenAI (GPT)" />
          <Tab label="Anthropic (Claude)" />
        </Tabs>

        {/* OpenAI Tab */}
        {activeTab === 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              OpenAI Configuration
            </Typography>
            
            <Typography variant="body2" color="text.secondary" paragraph>
              OpenAI API keys enable access to GPT models for agent evaluations.{' '}
              <Link 
                href="https://platform.openai.com/api-keys" 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
              >
                Get your API key here
                <OpenInNewIcon fontSize="small" />
              </Link>
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Current Status:
              </Typography>
              {isLoading ? (
                <Typography variant="body2">Loading...</Typography>
              ) : (
                renderKeyStatus(keyStatus?.openai_configured || false, keyStatus?.openai_key_preview)
              )}
            </Box>

            <TextField
              fullWidth
              label="OpenAI API Key"
              type={showOpenaiKey ? 'text' : 'password'}
              value={openaiKey}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOpenaiKey(e.target.value)}
              placeholder="sk-..."
              sx={{ mb: 2 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                      edge="end"
                    >
                      {showOpenaiKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                onClick={handleSaveOpenAI}
                disabled={!openaiKey.trim() || updateKeysMutation.isPending}
              >
                Save OpenAI Key
              </Button>
              <Button
                variant="outlined"
                color="error"
                onClick={handleClearOpenAI}
                disabled={!keyStatus?.openai_configured || updateKeysMutation.isPending}
              >
                Clear Key
              </Button>
            </Box>
          </Box>
        )}

        {/* Anthropic Tab */}
        {activeTab === 1 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Anthropic Configuration
            </Typography>
            
            <Typography variant="body2" color="text.secondary" paragraph>
              Anthropic API keys enable access to Claude models for agent evaluations.{' '}
              <Link 
                href="https://console.anthropic.com/" 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
              >
                Get your API key here
                <OpenInNewIcon fontSize="small" />
              </Link>
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Current Status:
              </Typography>
              {isLoading ? (
                <Typography variant="body2">Loading...</Typography>
              ) : (
                renderKeyStatus(keyStatus?.anthropic_configured || false, keyStatus?.anthropic_key_preview)
              )}
            </Box>

            <TextField
              fullWidth
              label="Anthropic API Key"
              type={showAnthropicKey ? 'text' : 'password'}
              value={anthropicKey}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAnthropicKey(e.target.value)}
              placeholder="ant-..."
              sx={{ mb: 2 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowAnthropicKey(!showAnthropicKey)}
                      edge="end"
                    >
                      {showAnthropicKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                onClick={handleSaveAnthropic}
                disabled={!anthropicKey.trim() || updateKeysMutation.isPending}
              >
                Save Anthropic Key
              </Button>
              <Button
                variant="outlined"
                color="error"
                onClick={handleClearAnthropic}
                disabled={!keyStatus?.anthropic_configured || updateKeysMutation.isPending}
              >
                Clear Key
              </Button>
            </Box>
          </Box>
        )}

        {updateKeysMutation.error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {updateKeysMutation.error.message}
          </Alert>
        )}

        {updateKeysMutation.isSuccess && (
          <Alert severity="success" sx={{ mt: 2 }}>
            API keys updated successfully!
          </Alert>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default APIKeyManager;