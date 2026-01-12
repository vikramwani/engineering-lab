import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Grid,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
  Chip,
} from '@mui/material';
import {
  PanTool as PanToolIcon,
  Send as SendIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';

import HITLEscalationAlert from '../components/HITLEscalationAlert';
import AgentDecisionCard from '../components/AgentDecisionCard';

interface HITLRequest {
  request_id: string;
  task_id: string;
  alignment_state: string;
  escalation_reason: string;
  summary: string;
  agent_decisions: any[];
  dissenting_agents?: string[];
  created_at: string;
  status: string;
  review?: any;
}

interface ReviewFormData {
  decision_value: any;
  confidence: number;
  rationale: string;
  evidence: string[];
}

const HITLPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedRequest, setSelectedRequest] = useState<HITLRequest | null>(null);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [reviewForm, setReviewForm] = useState<ReviewFormData>({
    decision_value: '',
    confidence: 0.8,
    rationale: '',
    evidence: [],
  });

  const queryClient = useQueryClient();

  const { data: hitlData, isLoading } = useQuery({
    queryKey: ['hitl-requests'],
    queryFn: async () => {
      const response = await fetch('/api/hitl/requests');
      return response.json();
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const reviewMutation = useMutation({
    mutationFn: async ({ requestId, review }: { requestId: string; review: any }) => {
      const response = await fetch(`/api/hitl/requests/${requestId}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...review,
          reviewer_id: 'current-user', // In real app, get from auth context
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to submit review');
      }
      
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hitl-requests'] });
      setReviewDialogOpen(false);
      setSelectedRequest(null);
      setReviewForm({
        decision_value: '',
        confidence: 0.8,
        rationale: '',
        evidence: [],
      });
    },
  });

  const handleStartReview = (request: HITLRequest) => {
    setSelectedRequest(request);
    
    // Pre-populate form with judge agent's decision if available
    const judgeDecision = request.agent_decisions.find(d => d.role_type === 'judge');
    if (judgeDecision) {
      setReviewForm({
        decision_value: judgeDecision.decision_value,
        confidence: judgeDecision.confidence,
        rationale: judgeDecision.rationale || '',
        evidence: judgeDecision.evidence || [],
      });
    }
    
    setReviewDialogOpen(true);
  };

  const handleSubmitReview = () => {
    if (!selectedRequest) return;
    
    reviewMutation.mutate({
      requestId: selectedRequest.request_id,
      review: reviewForm,
    });
  };

  const handleAddEvidence = () => {
    const evidence = prompt('Enter evidence item:');
    if (evidence) {
      setReviewForm({
        ...reviewForm,
        evidence: [...reviewForm.evidence, evidence],
      });
    }
  };

  const handleRemoveEvidence = (index: number) => {
    setReviewForm({
      ...reviewForm,
      evidence: reviewForm.evidence.filter((_, i) => i !== index),
    });
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  const pendingRequests = hitlData?.requests.filter((req: HITLRequest) => req.status === 'pending') || [];
  const reviewedRequests = hitlData?.requests.filter((req: HITLRequest) => req.status === 'reviewed') || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Human-in-the-Loop Reviews
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Review and resolve agent disagreements that require human judgment.
      </Typography>

      <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab 
          label={`Pending Reviews (${pendingRequests.length})`} 
          icon={<PanToolIcon />} 
          iconPosition="start"
        />
        <Tab 
          label={`Completed Reviews (${reviewedRequests.length})`} 
          icon={<CheckCircleIcon />} 
          iconPosition="start"
        />
      </Tabs>

      {/* Pending Reviews Tab */}
      {activeTab === 0 && (
        <Box>
          {pendingRequests.length === 0 ? (
            <Alert severity="info">
              No pending reviews. All agent evaluations are currently aligned.
            </Alert>
          ) : (
            pendingRequests.map((request: HITLRequest) => (
              <HITLEscalationAlert
                key={request.request_id}
                request={request}
                onReview={() => handleStartReview(request)}
                severity="high"
              />
            ))
          )}
        </Box>
      )}

      {/* Completed Reviews Tab */}
      {activeTab === 1 && (
        <Box>
          {reviewedRequests.length === 0 ? (
            <Alert severity="info">
              No completed reviews yet.
            </Alert>
          ) : (
            <Grid container spacing={2}>
              {reviewedRequests.map((request: HITLRequest) => (
                <Grid item xs={12} key={request.request_id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                        <Box>
                          <Typography variant="h6">
                            {request.task_id}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Reviewed: {request.review ? new Date(request.review.reviewed_at).toLocaleString() : 'N/A'}
                          </Typography>
                        </Box>
                        <Chip label="Reviewed" color="success" />
                      </Box>
                      
                      {request.review && (
                        <Box sx={{ p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Human Decision
                          </Typography>
                          <Typography variant="body2">
                            <strong>Decision:</strong> {String(request.review.decision_value)}
                          </Typography>
                          <Typography variant="body2">
                            <strong>Confidence:</strong> {(request.review.confidence * 100).toFixed(0)}%
                          </Typography>
                          <Typography variant="body2">
                            <strong>Rationale:</strong> {request.review.rationale}
                          </Typography>
                          <Typography variant="body2">
                            <strong>Reviewer:</strong> {request.review.reviewer_id}
                          </Typography>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      )}

      {/* Review Dialog */}
      <Dialog
        open={reviewDialogOpen}
        onClose={() => setReviewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Human Review - {selectedRequest?.request_id}
        </DialogTitle>
        
        <DialogContent>
          {selectedRequest && (
            <Box>
              {/* Request Summary */}
              <Alert severity="warning" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>Escalation Reason:</strong> {selectedRequest.escalation_reason}
                </Typography>
                <Typography variant="body2">
                  {selectedRequest.summary}
                </Typography>
              </Alert>

              {/* Agent Decisions */}
              <Typography variant="h6" gutterBottom>
                Agent Decisions
              </Typography>
              {selectedRequest.agent_decisions.map((decision, index) => (
                <AgentDecisionCard
                  key={index}
                  decision={decision}
                  showEvidence={true}
                  expandable={false}
                />
              ))}

              {/* Review Form */}
              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Your Decision
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Decision Value"
                    value={reviewForm.decision_value}
                    onChange={(e) => setReviewForm({ ...reviewForm, decision_value: e.target.value })}
                    placeholder="Enter your decision..."
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <Typography gutterBottom>
                    Confidence: {(reviewForm.confidence * 100).toFixed(0)}%
                  </Typography>
                  <Slider
                    value={reviewForm.confidence}
                    onChange={(_, value) => setReviewForm({ ...reviewForm, confidence: value as number })}
                    min={0}
                    max={1}
                    step={0.05}
                    marks={[
                      { value: 0, label: '0%' },
                      { value: 0.5, label: '50%' },
                      { value: 1, label: '100%' },
                    ]}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Rationale"
                    value={reviewForm.rationale}
                    onChange={(e) => setReviewForm({ ...reviewForm, rationale: e.target.value })}
                    placeholder="Explain your reasoning..."
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2">
                      Evidence ({reviewForm.evidence.length} items)
                    </Typography>
                    <Button size="small" onClick={handleAddEvidence}>
                      Add Evidence
                    </Button>
                  </Box>
                  {reviewForm.evidence.map((evidence, index) => (
                    <Chip
                      key={index}
                      label={evidence}
                      onDelete={() => handleRemoveEvidence(index)}
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setReviewDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmitReview}
            disabled={!reviewForm.decision_value || !reviewForm.rationale || reviewMutation.isPending}
            startIcon={reviewMutation.isPending ? <CircularProgress size={20} /> : <SendIcon />}
          >
            Submit Review
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HITLPage;