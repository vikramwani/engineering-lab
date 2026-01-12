import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Assessment as AssessmentIcon,
  PanTool as PanToolIcon,
  History as HistoryIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import HITLEscalationAlert from '../components/HITLEscalationAlert';

interface DashboardStats {
  total_evaluations: number;
  pending_hitl_requests: number;
  recent_evaluations: any[];
  alignment_distribution: Record<string, number>;
}

const fetchDashboardStats = async (): Promise<DashboardStats> => {
  const [evaluationsResponse, hitlResponse] = await Promise.all([
    fetch('/api/evaluations'),
    fetch('/api/hitl/requests'),
  ]);

  const evaluations = await evaluationsResponse.json();
  const hitlRequests = await hitlResponse.json();

  // Calculate alignment distribution
  const alignmentDistribution: Record<string, number> = {};
  const evaluationsList = evaluations?.evaluations || [];
  evaluationsList.forEach((evaluation: any) => {
    const state = evaluation.alignment_summary?.state || 'unknown';
    alignmentDistribution[state] = (alignmentDistribution[state] || 0) + 1;
  });

  return {
    total_evaluations: evaluations?.total || 0,
    pending_hitl_requests: hitlRequests?.requests?.filter((req: any) => req.status === 'pending').length || 0,
    recent_evaluations: evaluationsList.slice(-5).reverse(),
    alignment_distribution: alignmentDistribution,
  };
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: hitlRequests } = useQuery({
    queryKey: ['hitl-requests'],
    queryFn: async () => {
      const response = await fetch('/api/hitl/requests');
      return response.json();
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load dashboard data. Please try again later.
      </Alert>
    );
  }

  const pendingHitlRequests = hitlRequests?.requests?.filter((req: any) => req.status === 'pending') || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Monitor agent alignment evaluations and manage human-in-the-loop reviews.
      </Typography>

      {/* HITL Alerts */}
      {pendingHitlRequests.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Pending Reviews ({pendingHitlRequests.length})
          </Typography>
          {pendingHitlRequests.slice(0, 3).map((request: any) => (
            <HITLEscalationAlert
              key={request.request_id}
              request={request}
              onReview={(requestId) => navigate(`/hitl?request=${requestId}`)}
              severity="high"
            />
          ))}
          {pendingHitlRequests.length > 3 && (
            <Button
              variant="outlined"
              onClick={() => navigate('/hitl')}
              sx={{ mt: 1 }}
            >
              View All {pendingHitlRequests.length} Pending Reviews
            </Button>
          )}
        </Box>
      )}

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AssessmentIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Evaluations</Typography>
              </Box>
              <Typography variant="h3" color="primary">
                {stats?.total_evaluations || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PanToolIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6">Pending Reviews</Typography>
              </Box>
              <Typography variant="h3" color="warning.main">
                {stats?.pending_hitl_requests || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Alignment Rate</Typography>
              </Box>
              <Typography variant="h3" color="success.main">
                {stats?.alignment_distribution?.full_alignment 
                  ? Math.round((stats.alignment_distribution.full_alignment / stats.total_evaluations) * 100)
                  : 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <HistoryIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">Recent Activity</Typography>
              </Box>
              <Typography variant="h3" color="info.main">
                {stats?.recent_evaluations?.length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<PlayArrowIcon />}
                  onClick={() => navigate('/evaluate')}
                  size="large"
                >
                  Start New Evaluation
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<PanToolIcon />}
                  onClick={() => navigate('/hitl')}
                  disabled={!stats?.pending_hitl_requests}
                >
                  Review HITL Requests ({stats?.pending_hitl_requests || 0})
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<HistoryIcon />}
                  onClick={() => navigate('/history')}
                >
                  View Evaluation History
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Alignment Distribution
              </Typography>
              {stats?.alignment_distribution && Object.keys(stats.alignment_distribution).length > 0 ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {Object.entries(stats.alignment_distribution).map(([state, count]) => (
                    <Box key={state} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Chip
                        label={state.replace('_', ' ').toUpperCase()}
                        size="small"
                        color={
                          state === 'full_alignment' ? 'success' :
                          state === 'soft_disagreement' ? 'warning' :
                          state === 'hard_disagreement' ? 'error' : 'default'
                        }
                      />
                      <Typography variant="body2">
                        {count} ({Math.round((count / stats.total_evaluations) * 100)}%)
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No evaluations yet. Start your first evaluation to see alignment patterns.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Evaluations */}
      {stats?.recent_evaluations && stats.recent_evaluations.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Evaluations
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {stats.recent_evaluations.map((evaluation: any) => (
                <Box
                  key={evaluation.task_id}
                  sx={{
                    p: 2,
                    border: '1px solid #e0e0e0',
                    borderRadius: 1,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Box>
                    <Typography variant="subtitle2">
                      {evaluation.task_id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {evaluation.task_type} • {new Date(evaluation.created_at).toLocaleString()}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={evaluation.alignment_summary?.state?.replace('_', ' ') || 'Unknown'}
                      size="small"
                      color={
                        evaluation.alignment_summary?.state === 'full_alignment' ? 'success' :
                        evaluation.alignment_summary?.state === 'soft_disagreement' ? 'warning' :
                        evaluation.alignment_summary?.state === 'hard_disagreement' ? 'error' : 'default'
                      }
                    />
                    <Typography variant="body2">
                      {(evaluation.confidence * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default Dashboard;