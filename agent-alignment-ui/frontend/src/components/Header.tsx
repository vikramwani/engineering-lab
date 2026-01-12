import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Badge,
  Tooltip,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Key as KeyIcon,
} from '@mui/icons-material';

import APIKeyManager from './APIKeyManager';

const Header: React.FC = () => {
  const [apiKeyDialogOpen, setApiKeyDialogOpen] = useState(false);

  return (
    <>
      <AppBar position="static" color="primary" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Agent Alignment Framework
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Configure API Keys">
              <IconButton 
                color="inherit"
                onClick={() => setApiKeyDialogOpen(true)}
              >
                <KeyIcon />
              </IconButton>
            </Tooltip>
            
            <IconButton color="inherit">
              <Badge badgeContent={0} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
            
            <IconButton color="inherit">
              <SettingsIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      <APIKeyManager 
        open={apiKeyDialogOpen}
        onClose={() => setApiKeyDialogOpen(false)}
      />
    </>
  );
};

export default Header;