import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
  Grid,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

interface AlignmentSummary {
  state: string;
  alignment_score?: number;
  decision_agreement: boolean;
  confidence_spread: number;
  confidence_distribution?: number[];
  avg_confidence: number;
  dissenting_agents?: string[];
  disagreement_areas: string[];
  consensus_strength?: number;
  resolution_rationale?: string;
}

interface AlignmentAnalysisProps {
  summary: AlignmentSummary;
  showCharts?: boolean;
  interactive?: boolean;
}

const getAlignmentIcon = (state: string) => {
  switch (state.toLowerCase()) {
    case 'full_alignment':
      return <CheckCircleIcon sx={{ color: '#4caf50' }} />;
    case 'soft_disagreement':
      return <WarningIcon sx={{ color: '#ff9800' }} />;
    case 'hard_disagreement':
      return <ErrorIcon sx={{ color: '#f44336' }} />;
    case 'insufficient_signal':
      return <HelpIcon sx={{ color: '#9e9e9e' }} />;
    default:
      return <HelpIcon sx={{ color: '#9e9e9e' }} />;
  }
};

const getAlignmentColor = (state: string) => {
  switch (state.toLowerCase()) {
    case 'full_alignment':
      return '#4caf50';
    case 'soft_disagreement':
      return '#ff9800';
    case 'hard_disagreement':
      return '#f44336';
    case 'insufficient_signal':
      return '#9e9e9e';
    default:
      return '#9e9e9e';
  }
};

const getAlignmentSeverity = (state: string): 'success' | 'warning' | 'error' | 'info' => {
  switch (state.toLowerCase()) {
    case 'full_alignment':
      return 'success';
    case 'soft_disagreement':
      return 'warning';
    case 'hard_disagreement':
      return 'error';
    case 'insufficient_signal':
      return 'info';
    default:
      return 'info';
  }
};

const AlignmentAnalysis: React.FC<AlignmentAnalysisProps> = ({
  summary,
  showCharts = true,
  interactive = true,
}) => {
  const alignmentColor = getAlignmentColor(summary.state);
  const alignmentIcon = getAlignmentIcon(summary.state);
  const severity = getAlignmentSeverity(summary.state);

  // Prepare chart data
  const confidenceData = summary.confidence_distribution
    ? summary.confidence_distribution.map((conf, index) => ({
        agent: `Agent ${index + 1}`,
        confidence: conf * 100,
      }))
    : [];

  const alignmentData = [
    { name: 'Agreement', value: summary.decision_agreement ? 1 : 0, color: '#4caf50' },
    { name: 'Disagreement', value: summary.decision_agreement ? 0 : 1, color: '#f44336' },
  ];

  return (
    <Card>
      <CardHeader
        avatar={alignmentIcon}
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6">Alignment Analysis</Typography>
            <Chip
              label={summary.state.replace('_', ' ').toUpperCase()}
              sx={{
                backgroundColor: alignmentColor,
                color: 'white',
                fontWeight: 'bold',
              }}
            />
          </Box>
        }
        subheader={`Average Confidence: ${(summary.avg_confidence * 100).toFixed(1)}%`}
      />
      
      <CardContent>
        <Alert severity={severity} sx={{ mb: 2 }}>
          <Typography variant="body2">
            {summary.state === 'full_alignment' && 'All agents are in agreement. High confidence in the result.'}
            {summary.state === 'soft_disagreement' && 'Minor disagreements detected. Review recommended.'}
            {summary.state === 'hard_disagreement' && 'Significant disagreements found. Human review required.'}
            {summary.state === 'insufficient_signal' && 'Low confidence signals. Additional evaluation may be needed.'}
          </Typography>
        </Alert>

        <Grid container spacing={3}>
          {/* Key Metrics */}
          <Grid item xs={12} md={6}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Decision Agreement
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={summary.decision_agreement ? 100 : 0}
                  sx={{
                    flexGrow: 1,
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: summary.decision_agreement ? '#4caf50' : '#f44336',
                    },
                  }}
                />
                <Typography variant="body2">
                  {summary.decision_agreement ? 'Yes' : 'No'}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Confidence Spread
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(summary.confidence_spread * 100, 100)}
                  sx={{
                    flexGrow: 1,
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: summary.confidence_spread > 0.3 ? '#f44336' : '#4caf50',
                    },
                  }}
                />
                <Typography variant="body2">
                  {(summary.confidence_spread * 100).toFixed(1)}%
                </Typography>
              </Box>
            </Box>

            {summary.consensus_strength !== undefined && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Consensus Strength
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={summary.consensus_strength * 100}
                    sx={{
                      flexGrow: 1,
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: '#e0e0e0',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: summary.consensus_strength > 0.7 ? '#4caf50' : '#ff9800',
                      },
                    }}
                  />
                  <Typography variant="body2">
                    {(summary.consensus_strength * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
            )}
          </Grid>

          {/* Charts */}
          {showCharts && (
            <Grid item xs={12} md={6}>
              {confidenceData.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Confidence Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={150}>
                    <BarChart data={confidenceData}>
                      <XAxis dataKey="agent" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip formatter={(value) => [`${value}%`, 'Confidence']} />
                      <Bar dataKey="confidence" fill="#2196f3" />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              )}

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Agreement Overview
                </Typography>
                <ResponsiveContainer width="100%" height={120}>
                  <PieChart>
                    <Pie
                      data={alignmentData}
                      cx="50%"
                      cy="50%"
                      innerRadius={30}
                      outerRadius={50}
                      dataKey="value"
                    >
                      {alignmentData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </Grid>
          )}
        </Grid>

        {/* Disagreement Areas */}
        {summary.disagreement_areas && summary.disagreement_areas.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Disagreement Areas
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {summary.disagreement_areas.map((area, index) => (
                <Chip
                  key={index}
                  label={area.replace('_', ' ')}
                  size="small"
                  color="warning"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Dissenting Agents */}
        {summary.dissenting_agents && summary.dissenting_agents.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Dissenting Agents
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {summary.dissenting_agents.map((agent, index) => (
                <Chip
                  key={index}
                  label={agent}
                  size="small"
                  color="error"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Resolution Rationale */}
        {summary.resolution_rationale && (
          <Box sx={{ mt: 2, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              Resolution Rationale
            </Typography>
            <Typography variant="body2">
              {summary.resolution_rationale}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AlignmentAnalysis;