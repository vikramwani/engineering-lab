import React, { useState } from 'react';
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Chip,
  Divider,
} from '@mui/material';
import {
  PanTool as PanToolIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';

interface HITLRequest {
  request_id: string;
  task_id: string;
  alignment_state: string;
  alignment_score?: number;
  escalation_reason: string;
  summary: string;
  agent_decisions: any[];
  dissenting_agents?: string[];
  created_at: string;
  metadata?: Record<string, any>;
  status: string;
}

interface HITLEscalationAlertProps {
  request: HITLRequest;
  onReview?: (requestId: string) => void;
  severity?: 'low' | 'medium' | 'high';
  compact?: boolean;
}

const getSeverityColor = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'high':
      return 'error';
    case 'medium':
      return 'warning';
    case 'low':
      return 'info';
    default:
      return 'warning';
  }
};

const getEscalationReasonLabel = (reason: string) => {
  switch (reason.toLowerCase()) {
    case 'hard_disagreement':
      return 'Hard Disagreement';
    case 'soft_disagreement':
      return 'Soft Disagreement';
    case 'insufficient_signal':
      return 'Insufficient Signal';
    case 'low_confidence':
      return 'Low Confidence';
    case 'policy_violation':
      return 'Policy Violation';
    default:
      return reason.replace('_', ' ').toUpperCase();
  }
};

const HITLEscalationAlert: React.FC<HITLEscalationAlertProps> = ({
  request,
  onReview,
  severity = 'medium',
  compact = false,
}) => {
  const [detailsOpen, setDetailsOpen] = useState(false);

  const severityColor = getSeverityColor(severity) as 'error' | 'warning' | 'info';
  const escalationLabel = getEscalationReasonLabel(request.escalation_reason);

  const handleReview = () => {
    if (onReview) {
      onReview(request.request_id);
    }
  };

  const handleViewDetails = () => {
    setDetailsOpen(true);
  };

  return (
    <>
      <Alert
        severity={severityColor}
        icon={<PanToolIcon />}
        action={
          <Box sx={{ display: 'flex', gap: 1 }}>
            {!compact && (
              <Button
                color="inherit"
                size="small"
                startIcon={<VisibilityIcon />}
                onClick={handleViewDetails}
              >
                Details
              </Button>
            )}
            <Button
              color="inherit"
              size="small"
              variant="outlined"
              onClick={handleReview}
              disabled={request.status === 'reviewed'}
            >
              {request.status === 'reviewed' ? 'Reviewed' : 'Review'}
            </Button>
          </Box>
        }
        sx={{ mb: 2 }}
      >
        <AlertTitle>
          Human Review Required - {escalationLabel}
        </AlertTitle>
        
        {!compact && (
          <>
            <Typography variant="body2" sx={{ mb: 1 }}>
              {request.summary}
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
              <Chip
                label={`Task: ${request.task_id}`}
                size="small"
                variant="outlined"
              />
              <Chip
                label={`State: ${request.alignment_state}`}
                size="small"
                color={severityColor}
                variant="outlined"
              />
              {request.dissenting_agents && request.dissenting_agents.length > 0 && (
                <Chip
                  label={`${request.dissenting_agents.length} Dissenting Agent(s)`}
                  size="small"
                  color="error"
                  variant="outlined"
                />
              )}
            </Box>
          </>
        )}
      </Alert>

      {/* Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          HITL Request Details - {request.request_id}
        </DialogTitle>
        
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Request Information
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Task ID:</strong> {request.task_id}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Created:</strong> {new Date(request.created_at).toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Status:</strong> {request.status}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Alignment State:</strong> {request.alignment_state}
            </Typography>
            {request.alignment_score !== undefined && (
              <Typography variant="body2" color="text.secondary">
                <strong>Alignment Score:</strong> {(request.alignment_score * 100).toFixed(1)}%
              </Typography>
            )}
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Escalation Reason
            </Typography>
            <Chip
              label={escalationLabel}
              color={severityColor}
              sx={{ mb: 1 }}
            />
            <Typography variant="body2">
              {request.summary}
            </Typography>
          </Box>

          {request.dissenting_agents && request.dissenting_agents.length > 0 && (
            <>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Dissenting Agents
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {request.dissenting_agents.map((agent, index) => (
                    <Chip
                      key={index}
                      label={agent}
                      color="error"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>
            </>
          )}

          <Divider sx={{ my: 2 }} />

          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Agent Decisions ({request.agent_decisions.length})
            </Typography>
            {request.agent_decisions.map((decision, index) => (
              <Box
                key={index}
                sx={{
                  p: 2,
                  mb: 1,
                  border: '1px solid #e0e0e0',
                  borderRadius: 1,
                  backgroundColor: '#f9f9f9',
                }}
              >
                <Typography variant="subtitle2">
                  {decision.agent_name} ({decision.role_type})
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Decision: {String(decision.decision_value)} (Confidence: {(decision.confidence * 100).toFixed(1)}%)
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {decision.rationale}
                </Typography>
              </Box>
            ))}
          </Box>

          {request.metadata && Object.keys(request.metadata).length > 0 && (
            <>
              <Divider sx={{ my: 2 }} />
              <Box>
                <Typography variant="h6" gutterBottom>
                  Metadata
                </Typography>
                <Box
                  sx={{
                    p: 2,
                    backgroundColor: '#f5f5f5',
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                  }}
                >
                  <pre>{JSON.stringify(request.metadata, null, 2)}</pre>
                </Box>
              </Box>
            </>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>
            Close
          </Button>
          <Button
            variant="contained"
            onClick={handleReview}
            disabled={request.status === 'reviewed'}
          >
            {request.status === 'reviewed' ? 'Already Reviewed' : 'Start Review'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default HITLEscalationAlert;