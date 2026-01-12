import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Pagination,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  FilterList as FilterListIcon,
  Delete as DeleteIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';

import AgentDecisionCard from '../components/AgentDecisionCard';
import AlignmentAnalysis from '../components/AlignmentAnalysis';

interface EvaluationHistory {
  task_id: string;
  task_type: string;
  synthesized_decision: any;
  compatible?: boolean;
  relationship?: string;
  confidence: number;
  reasoning: string;
  agent_decisions: any[];
  alignment_summary: any;
  requires_human_review: boolean;
  processing_time_ms: number;
  created_at: string;
}

const HistoryPage: React.FC = () => {
  const [selectedEvaluation, setSelectedEvaluation] = useState<EvaluationHistory | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [filters, setFilters] = useState({
    task_type: '',
    alignment_state: '',
    search: '',
  });
  const [page, setPage] = useState(1);
  const itemsPerPage = 10;
  const [clearConfirmOpen, setClearConfirmOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const { data: evaluationsData, isLoading, error: queryError } = useQuery({
    queryKey: ['evaluations'],
    queryFn: async () => {
      const response = await fetch('/api/evaluations');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    },
    retry: 3,
    retryDelay: 1000,
  });

  const clearHistoryMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/evaluations', {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to clear evaluation history');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluations'] });
      setClearConfirmOpen(false);
    },
  });

  const deleteEvaluationMutation = useMutation({
    mutationFn: async (taskId: string) => {
      const response = await fetch(`/api/evaluations/${taskId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete evaluation');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluations'] });
    },
  });

  const handleViewDetails = (evaluation: EvaluationHistory) => {
    setSelectedEvaluation(evaluation);
    setDetailsOpen(true);
  };

  const handleExport = (evaluation: EvaluationHistory) => {
    const dataStr = JSON.stringify(evaluation, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `evaluation-${evaluation.task_id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleDeleteEvaluation = (taskId: string) => {
    deleteEvaluationMutation.mutate(taskId);
  };

  const handleClearHistory = () => {
    clearHistoryMutation.mutate();
  };

  // Handle query errors
  if (queryError) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Evaluation History
        </Typography>
        <Alert severity="error">
          Failed to load evaluation history: {queryError.message}
        </Alert>
        <Button 
          variant="outlined" 
          onClick={() => window.location.reload()} 
          sx={{ mt: 2 }}
        >
          Retry
        </Button>
      </Box>
    );
  }

  // Handle component errors
  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Evaluation History
        </Typography>
        <Alert severity="error">
          Component error: {error}
        </Alert>
        <Button 
          variant="outlined" 
          onClick={() => setError(null)} 
          sx={{ mt: 2 }}
        >
          Reset
        </Button>
      </Box>
    );
  }

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Comprehensive null checks with error handling
  let evaluations: EvaluationHistory[] = [];
  let filteredEvaluations: EvaluationHistory[] = [];
  let paginatedEvaluations: EvaluationHistory[] = [];
  let taskTypes: string[] = [];
  let alignmentStates: string[] = [];
  let totalPages = 1;

  try {
    if (!evaluationsData) {
      return (
        <Box>
          <Typography variant="h4" gutterBottom>
            Evaluation History
          </Typography>
          <Alert severity="info">
            Loading evaluation data...
          </Alert>
        </Box>
      );
    }

    evaluations = Array.isArray(evaluationsData?.evaluations) ? evaluationsData.evaluations : [];

    // Ensure all evaluations have required properties
    evaluations = evaluations.filter((evaluation) => {
      return evaluation && 
             typeof evaluation === 'object' && 
             evaluation.task_id && 
             evaluation.task_type;
    });

    // Apply filters (with safety checks)
    filteredEvaluations = evaluations.filter((evaluation: EvaluationHistory) => {
      try {
        const matchesTaskType = !filters.task_type || evaluation.task_type === filters.task_type;
        const matchesAlignmentState = !filters.alignment_state || 
          evaluation.alignment_summary?.state === filters.alignment_state;
        const matchesSearch = !filters.search || 
          (evaluation.task_id && evaluation.task_id.toLowerCase().includes(filters.search.toLowerCase())) ||
          (evaluation.task_type && evaluation.task_type.toLowerCase().includes(filters.search.toLowerCase()));
        
        return matchesTaskType && matchesAlignmentState && matchesSearch;
      } catch (e) {
        console.warn('Error filtering evaluation:', e, evaluation);
        return false;
      }
    });

    // Pagination
    totalPages = Math.max(1, Math.ceil(filteredEvaluations.length / itemsPerPage));
    paginatedEvaluations = filteredEvaluations.slice(
      (page - 1) * itemsPerPage,
      page * itemsPerPage
    );

    // Get unique values for filters (with additional safety checks)
    try {
      taskTypes = evaluations.length > 0 
        ? [...new Set(evaluations.map((evaluation: EvaluationHistory) => evaluation?.task_type).filter(Boolean))] as string[]
        : [];
      alignmentStates = evaluations.length > 0
        ? [...new Set(evaluations.map((evaluation: EvaluationHistory) => evaluation?.alignment_summary?.state).filter(Boolean))] as string[]
        : [];
    } catch (e) {
      console.warn('Error computing filter options:', e);
      taskTypes = [];
      alignmentStates = [];
    }

  } catch (e) {
    console.error('Error processing evaluation data:', e);
    const errorMessage = e instanceof Error ? e.message : 'Unknown error';
    setError(`Data processing error: ${errorMessage}`);
    return null;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Evaluation History
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Browse and analyze past multi-agent evaluations.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<ClearIcon />}
            onClick={() => setClearConfirmOpen(true)}
            disabled={evaluations.length === 0 || clearHistoryMutation.isPending}
          >
            Clear History
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <FilterListIcon />
            <Typography variant="h6">Filters</Typography>
          </Box>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Search"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                placeholder="Search by task ID or type..."
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Task Type</InputLabel>
                <Select
                  value={filters.task_type}
                  label="Task Type"
                  onChange={(e) => setFilters({ ...filters, task_type: e.target.value })}
                >
                  <MenuItem value="">All Types</MenuItem>
                  {taskTypes.map((type: string) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Alignment State</InputLabel>
                <Select
                  value={filters.alignment_state}
                  label="Alignment State"
                  onChange={(e) => setFilters({ ...filters, alignment_state: e.target.value })}
                >
                  <MenuItem value="">All States</MenuItem>
                  {alignmentStates.map((state: string) => (
                    <MenuItem key={state} value={state}>
                      {state.replace('_', ' ').toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Results */}
      {filteredEvaluations.length === 0 ? (
        <Alert severity="info">
          No evaluations found matching your criteria.
        </Alert>
      ) : (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Showing {paginatedEvaluations.length} of {filteredEvaluations.length} evaluations
          </Typography>
          
          <Grid container spacing={2}>
            {paginatedEvaluations.map((evaluation: EvaluationHistory) => (
              <Grid item xs={12} key={evaluation.task_id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6">
                          {evaluation.task_id}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {evaluation.task_type} • {new Date(evaluation.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                          size="small"
                          startIcon={<VisibilityIcon />}
                          onClick={() => handleViewDetails(evaluation)}
                        >
                          View
                        </Button>
                        <Button
                          size="small"
                          startIcon={<DownloadIcon />}
                          onClick={() => handleExport(evaluation)}
                        >
                          Export
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          startIcon={<DeleteIcon />}
                          onClick={() => handleDeleteEvaluation(evaluation.task_id)}
                          disabled={deleteEvaluationMutation.isPending}
                        >
                          Delete
                        </Button>
                      </Box>
                    </Box>
                    
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      <Chip
                        label={evaluation.alignment_summary?.state?.replace('_', ' ').toUpperCase() || 'Unknown'}
                        color={
                          evaluation.alignment_summary?.state === 'full_alignment' ? 'success' :
                          evaluation.alignment_summary?.state === 'soft_disagreement' ? 'warning' :
                          evaluation.alignment_summary?.state === 'hard_disagreement' ? 'error' : 'default'
                        }
                        size="small"
                      />
                      <Chip
                        label={`${(evaluation.confidence * 100).toFixed(0)}% Confidence`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`${(evaluation.agent_decisions?.length || 0)} Agents`}
                        size="small"
                        variant="outlined"
                      />
                      {evaluation.requires_human_review && (
                        <Chip
                          label="HITL Required"
                          color="warning"
                          size="small"
                        />
                      )}
                    </Box>
                    
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Decision:</strong> {(() => {
                        const compatible = evaluation.compatible;
                        const relationship = evaluation.synthesized_decision || evaluation.relationship;
                        
                        if (compatible === true) {
                          const relationshipFormatted = relationship 
                            ? relationship.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
                            : 'Compatible';
                          return `Compatible (${relationshipFormatted})`;
                        } else if (compatible === false) {
                          return 'Not Compatible';
                        } else {
                          // Fallback to original display
                          return String(relationship || 'Unknown');
                        }
                      })()}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary">
                      {evaluation.reasoning && evaluation.reasoning.length > 150 
                        ? `${evaluation.reasoning.substring(0, 150)}...`
                        : evaluation.reasoning || 'No reasoning provided'
                      }
                    </Typography>
                    
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                      Processing Time: {evaluation.processing_time_ms}ms
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
          
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, newPage) => setPage(newPage)}
                color="primary"
              />
            </Box>
          )}
        </>
      )}

      {/* Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Evaluation Details - {selectedEvaluation?.task_id}
        </DialogTitle>
        
        <DialogContent>
          {selectedEvaluation && (
            <Box>
              {/* Summary */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Final Decision
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Typography variant="h4">
                      {(() => {
                        const compatible = selectedEvaluation.compatible;
                        const relationship = selectedEvaluation.synthesized_decision || selectedEvaluation.relationship;
                        
                        if (compatible === true) {
                          const relationshipFormatted = relationship 
                            ? relationship.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
                            : 'Compatible';
                          return `Compatible (${relationshipFormatted})`;
                        } else if (compatible === false) {
                          return 'Not Compatible';
                        } else {
                          // Fallback to original display
                          return String(relationship || 'Unknown');
                        }
                      })()}
                    </Typography>
                    <Chip
                      label={`${(selectedEvaluation.confidence * 100).toFixed(0)}% Confidence`}
                      color={selectedEvaluation.confidence > 0.8 ? 'success' : 'warning'}
                    />
                  </Box>
                  <Typography variant="body1" paragraph>
                    {selectedEvaluation.reasoning}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Task Type: {selectedEvaluation.task_type} • 
                    Processing Time: {selectedEvaluation.processing_time_ms}ms • 
                    Created: {new Date(selectedEvaluation.created_at).toLocaleString()}
                  </Typography>
                </CardContent>
              </Card>

              {/* Alignment Analysis */}
              <Box sx={{ mb: 3 }}>
                <AlignmentAnalysis summary={selectedEvaluation.alignment_summary} />
              </Box>

              {/* Agent Decisions */}
              <Typography variant="h6" gutterBottom>
                Agent Decisions ({selectedEvaluation.agent_decisions?.length || 0})
              </Typography>
              {selectedEvaluation.agent_decisions?.map((decision, index) => (
                <AgentDecisionCard
                  key={index}
                  decision={decision}
                  showEvidence={true}
                  expandable={true}
                />
              )) || (
                <Alert severity="info">No agent decisions available</Alert>
              )}
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>
            Close
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => selectedEvaluation && handleExport(selectedEvaluation)}
          >
            Export JSON
          </Button>
        </DialogActions>
      </Dialog>

      {/* Clear History Confirmation Dialog */}
      <Dialog
        open={clearConfirmOpen}
        onClose={() => setClearConfirmOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Clear Evaluation History
        </DialogTitle>
        
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This action cannot be undone. All evaluation history will be permanently deleted.
          </Alert>
          <Typography>
            Are you sure you want to clear all {evaluations.length} evaluations from the history?
          </Typography>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setClearConfirmOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleClearHistory}
            color="error"
            variant="contained"
            disabled={clearHistoryMutation.isPending}
          >
            {clearHistoryMutation.isPending ? 'Clearing...' : 'Clear All'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HistoryPage;