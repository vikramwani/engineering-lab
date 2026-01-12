import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Chip,
  Box,
  Collapse,
  IconButton,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Person as PersonIcon,
  Psychology as PsychologyIcon,
  Gavel as GavelIcon,
  Science as ScienceIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

interface AgentDecision {
  agent_name: string;
  role_type: string;
  decision_value: any;
  compatible?: boolean;
  confidence: number;
  rationale: string;
  evidence: string[];
  metadata?: Record<string, any>;
}

interface AgentDecisionCardProps {
  decision: AgentDecision;
  showEvidence?: boolean;
  expandable?: boolean;
}

const ExpandMore = styled((props: { expand: boolean } & any) => {
  const { expand, ...other } = props;
  return <IconButton {...other} />;
})(({ theme, expand }) => ({
  transform: !expand ? 'rotate(0deg)' : 'rotate(180deg)',
  marginLeft: 'auto',
  transition: theme.transitions.create('transform', {
    duration: theme.transitions.duration.shortest,
  }),
}));

const getRoleIcon = (roleType: string) => {
  switch (roleType.toLowerCase()) {
    case 'advocate':
      return <PersonIcon />;
    case 'skeptic':
      return <PsychologyIcon />;
    case 'judge':
      return <GavelIcon />;
    case 'expert':
      return <ScienceIcon />;
    default:
      return <PersonIcon />;
  }
};

const getRoleColor = (roleType: string) => {
  switch (roleType.toLowerCase()) {
    case 'advocate':
      return '#4caf50';
    case 'skeptic':
      return '#f44336';
    case 'judge':
      return '#2196f3';
    case 'expert':
      return '#9c27b0';
    default:
      return '#757575';
  }
};

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return '#4caf50';
  if (confidence >= 0.6) return '#ff9800';
  if (confidence >= 0.4) return '#ff5722';
  return '#f44336';
};

const AgentDecisionCard: React.FC<AgentDecisionCardProps> = ({
  decision,
  showEvidence = true,
  expandable = true,
}) => {
  const [expanded, setExpanded] = useState(false);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  const roleColor = getRoleColor(decision.role_type);
  const confidenceColor = getConfidenceColor(decision.confidence);

  return (
    <Card sx={{ mb: 2, border: `2px solid ${roleColor}20` }}>
      <CardHeader
        avatar={
          <Box
            sx={{
              backgroundColor: roleColor,
              color: 'white',
              borderRadius: '50%',
              width: 40,
              height: 40,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {getRoleIcon(decision.role_type)}
          </Box>
        }
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6" component="div">
              {decision.agent_name}
            </Typography>
            <Chip
              label={decision.role_type}
              size="small"
              sx={{
                backgroundColor: roleColor,
                color: 'white',
                textTransform: 'capitalize',
              }}
            />
          </Box>
        }
        subheader={
          <Box sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Decision: <strong>{(() => {
                const compatible = decision.compatible;
                const decisionValue = decision.decision_value;
                
                if (compatible === true) {
                  const relationshipFormatted = decisionValue 
                    ? decisionValue.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
                    : 'Compatible';
                  return `Compatible (${relationshipFormatted})`;
                } else if (compatible === false) {
                  return 'Not Compatible';
                } else {
                  // Fallback to original display
                  return String(decisionValue || 'Unknown');
                }
              })()}</strong>
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Confidence:
              </Typography>
              <Box sx={{ flexGrow: 1, maxWidth: 100 }}>
                <LinearProgress
                  variant="determinate"
                  value={decision.confidence * 100}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: confidenceColor,
                    },
                  }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                {(decision.confidence * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Box>
        }
        action={
          expandable && (
            <ExpandMore
              expand={expanded}
              onClick={handleExpandClick}
              aria-expanded={expanded}
              aria-label="show more"
            >
              <ExpandMoreIcon />
            </ExpandMore>
          )
        }
      />
      
      <Collapse in={expanded || !expandable} timeout="auto" unmountOnExit>
        <CardContent sx={{ pt: 0 }}>
          <Typography variant="body2" color="text.secondary" paragraph>
            <strong>Rationale:</strong>
          </Typography>
          <Typography variant="body2" paragraph>
            {decision.rationale}
          </Typography>

          {showEvidence && decision.evidence && decision.evidence.length > 0 && (
            <>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                <strong>Evidence ({decision.evidence.length} items):</strong>
              </Typography>
              <List dense>
                {decision.evidence.map((evidence, index) => (
                  <ListItem key={index} sx={{ pl: 0 }}>
                    <ListItemText
                      primary={`${index + 1}. ${evidence}`}
                      primaryTypographyProps={{
                        variant: 'body2',
                      }}
                    />
                  </ListItem>
                ))}
              </List>
            </>
          )}

          {decision.metadata && Object.keys(decision.metadata).length > 0 && (
            <Box sx={{ mt: 2, p: 1, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Metadata: {JSON.stringify(decision.metadata, null, 2)}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Collapse>
    </Card>
  );
};

export default AgentDecisionCard;