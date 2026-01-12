import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Divider,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
  Key as KeyIcon,
} from '@mui/icons-material';

import AgentDecisionCard from '../components/AgentDecisionCard';
import AlignmentAnalysis from '../components/AlignmentAnalysis';
import HITLEscalationAlert from '../components/HITLEscalationAlert';
import APIKeyManager from '../components/APIKeyManager';

interface EvaluationFormData {
  task_type: string;
  decision_schema_type: string;
  evaluation_criteria: string;
  llm_provider: string;
  context: Record<string, any>;
}

interface Product {
  id: string;
  title: string;
  category: string;
  brand: string;
  attributes: Record<string, any>;
  description?: string;
}

const steps = ['Configure Task', 'Run Evaluation', 'Review Results'];

const sampleProducts: Product[] = [
  {
    id: 'iphone-15-pro-max',
    title: 'iPhone 15 Pro Max',
    category: 'Smartphone',
    brand: 'Apple',
    attributes: {
      screen_size: '6.7 inches',
      storage: '256GB',
      charging_ports: ['USB-C', 'MagSafe', 'Qi Wireless'],
      operating_system: 'iOS 17',
    },
    description: 'Latest iPhone with titanium design and A17 Pro chip.',
  },
  {
    id: 'magsafe-charger',
    title: 'Apple MagSafe Charger',
    category: 'Charger',
    brand: 'Apple',
    attributes: {
      power_output: '15W',
      connector_type: 'MagSafe magnetic',
      compatibility: ['iPhone 12 series', 'iPhone 13 series', 'iPhone 14 series', 'iPhone 15 series'],
    },
    description: 'Official Apple MagSafe wireless charger with magnetic alignment.',
  },
];

const EvaluationPage: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [apiKeyDialogOpen, setApiKeyDialogOpen] = useState(false);
  const [formData, setFormData] = useState<EvaluationFormData>({
    task_type: 'product_compatibility',
    decision_schema_type: 'categorical',
    evaluation_criteria: 'Determine if these products are compatible and classify their relationship type.',
    llm_provider: 'openai',
    context: {},
  });
  const [selectedProducts, setSelectedProducts] = useState<Product[]>([]);
  const [evaluationResult, setEvaluationResult] = useState<any>(null);

  // Fetch API key status
  const { data: keyStatus } = useQuery({
    queryKey: ['api-keys'],
    queryFn: async () => {
      const response = await fetch('/api/config/keys');
      if (!response.ok) {
        throw new Error('Failed to fetch API key status');
      }
      return response.json();
    },
  });

  const evaluationMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await fetch('/api/evaluations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error('Evaluation failed');
      }
      
      return response.json();
    },
    onSuccess: (result) => {
      setEvaluationResult(result);
      setActiveStep(2);
    },
  });

  const compatibilityMutation = useMutation({
    mutationFn: async (data: { product_a: Product; product_b: Product }) => {
      const response = await fetch('/api/evaluations/compatibility', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error('Compatibility evaluation failed');
      }
      
      return response.json();
    },
    onSuccess: (result) => {
      setEvaluationResult(result);
      setActiveStep(2);
    },
  });

  const handleProductSelect = (product: Product) => {
    if (selectedProducts.length < 2 && !selectedProducts.find(p => p.id === product.id)) {
      setSelectedProducts([...selectedProducts, product]);
    }
  };

  const handleProductRemove = (productId: string) => {
    setSelectedProducts(selectedProducts.filter(p => p.id !== productId));
  };

  const handleRunEvaluation = () => {
    if (formData.task_type === 'product_compatibility' && selectedProducts.length === 2) {
      // Use simplified compatibility endpoint
      compatibilityMutation.mutate({
        product_a: selectedProducts[0],
        product_b: selectedProducts[1],
      });
    } else {
      // Use general evaluation endpoint
      const evaluationData = {
        ...formData,
        context: {
          ...formData.context,
          products: selectedProducts,
        },
        decision_schema_config: 
          formData.decision_schema_type === 'categorical' 
            ? {
                categories: [
                  'replacement_filter',
                  'replacement_part',
                  'accessory',
                  'consumable',
                  'power_supply',
                  'not_compatible',
                  'insufficient_information',
                ],
              }
            : {},
      };
      
      evaluationMutation.mutate(evaluationData);
    }
    setActiveStep(1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setSelectedProducts([]);
    setEvaluationResult(null);
    evaluationMutation.reset();
    compatibilityMutation.reset();
  };

  const error = evaluationMutation.error || compatibilityMutation.error;

  // Check if API key is configured for selected provider
  const isApiKeyConfigured = formData.llm_provider === 'openai' 
    ? keyStatus?.openai_configured 
    : keyStatus?.anthropic_configured;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        New Evaluation
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Configure and run a new multi-agent evaluation with the Agent Alignment Framework.
      </Typography>

      {/* API Key Status Alert */}
      {!isApiKeyConfigured && (
        <Alert 
          severity="warning" 
          sx={{ mb: 3 }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              startIcon={<KeyIcon />}
              onClick={() => setApiKeyDialogOpen(true)}
            >
              Configure
            </Button>
          }
        >
          {formData.llm_provider === 'openai' ? 'OpenAI' : 'Anthropic'} API key is not configured. 
          Configure your API key to run evaluations.
        </Alert>
      )}

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error.message}
        </Alert>
      )}

      {/* Step 1: Configure Task */}
      {activeStep === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Configure Evaluation Task
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Task Type</InputLabel>
                  <Select
                    value={formData.task_type}
                    label="Task Type"
                    onChange={(e) => setFormData({ ...formData, task_type: e.target.value })}
                  >
                    <MenuItem value="product_compatibility">Product Compatibility</MenuItem>
                    <MenuItem value="content_moderation">Content Moderation</MenuItem>
                    <MenuItem value="risk_assessment">Risk Assessment</MenuItem>
                    <MenuItem value="custom">Custom</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Decision Schema</InputLabel>
                  <Select
                    value={formData.decision_schema_type}
                    label="Decision Schema"
                    onChange={(e) => setFormData({ ...formData, decision_schema_type: e.target.value })}
                  >
                    <MenuItem value="boolean">Boolean (Yes/No)</MenuItem>
                    <MenuItem value="categorical">Categorical (Multiple Options)</MenuItem>
                    <MenuItem value="scalar">Scalar (Numeric Range)</MenuItem>
                    <MenuItem value="freeform">Free Form (Text)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>LLM Provider</InputLabel>
                  <Select
                    value={formData.llm_provider}
                    label="LLM Provider"
                    onChange={(e) => setFormData({ ...formData, llm_provider: e.target.value })}
                  >
                    <MenuItem value="openai">OpenAI (GPT-4)</MenuItem>
                    <MenuItem value="anthropic">Anthropic (Claude)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Evaluation Criteria"
                  value={formData.evaluation_criteria}
                  onChange={(e) => setFormData({ ...formData, evaluation_criteria: e.target.value })}
                  placeholder="Describe what the agents should evaluate..."
                />
              </Grid>
            </Grid>

            {formData.task_type === 'product_compatibility' && (
              <>
                <Divider sx={{ my: 3 }} />
                <Typography variant="h6" gutterBottom>
                  Select Products to Compare
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Selected Products ({selectedProducts.length}/2):
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                    {selectedProducts.map((product) => (
                      <Chip
                        key={product.id}
                        label={product.title}
                        onDelete={() => handleProductRemove(product.id)}
                        color="primary"
                      />
                    ))}
                  </Box>
                </Box>

                <Grid container spacing={2}>
                  {sampleProducts.map((product) => (
                    <Grid item xs={12} md={6} key={product.id}>
                      <Card
                        sx={{
                          cursor: 'pointer',
                          border: selectedProducts.find(p => p.id === product.id) 
                            ? '2px solid #1976d2' 
                            : '1px solid #e0e0e0',
                          '&:hover': {
                            boxShadow: 2,
                          },
                        }}
                        onClick={() => handleProductSelect(product)}
                      >
                        <CardContent>
                          <Typography variant="h6">{product.title}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {product.brand} • {product.category}
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 1 }}>
                            {product.description}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </>
            )}

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                onClick={handleRunEvaluation}
                disabled={
                  !isApiKeyConfigured ||
                  (formData.task_type === 'product_compatibility' 
                    ? selectedProducts.length !== 2 
                    : !formData.evaluation_criteria.trim())
                }
                startIcon={<PlayArrowIcon />}
              >
                Run Evaluation
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Running Evaluation */}
      {activeStep === 1 && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Running Multi-Agent Evaluation
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Agents are analyzing the task and generating decisions...
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Results */}
      {activeStep === 2 && evaluationResult && (
        <Box>
          {/* HITL Alert */}
          {evaluationResult.requires_human_review && evaluationResult.hitl_request && (
            <HITLEscalationAlert
              request={evaluationResult.hitl_request}
              severity="high"
            />
          )}

          {/* Final Decision */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Final Decision
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Typography variant="h4">
                  {(() => {
                    const compatible = evaluationResult.compatible;
                    const relationship = evaluationResult.synthesized_decision || evaluationResult.relationship;
                    
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
                  label={`${(evaluationResult.confidence * 100).toFixed(0)}% Confidence`}
                  color={evaluationResult.confidence > 0.8 ? 'success' : 'warning'}
                />
              </Box>
              <Typography variant="body1" paragraph>
                {evaluationResult.reasoning}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Processing Time: {evaluationResult.processing_time_ms}ms
              </Typography>
            </CardContent>
          </Card>

          {/* Alignment Analysis */}
          <Box sx={{ mb: 3 }}>
            <AlignmentAnalysis summary={evaluationResult.alignment_summary} />
          </Box>

          {/* Agent Decisions */}
          <Typography variant="h6" gutterBottom>
            Agent Decisions ({evaluationResult.agent_decisions.length})
          </Typography>
          {evaluationResult.agent_decisions.map((decision: any, index: number) => (
            <AgentDecisionCard
              key={index}
              decision={decision}
              showEvidence={true}
              expandable={true}
            />
          ))}

          {/* Actions */}
          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              onClick={handleReset}
              startIcon={<RefreshIcon />}
            >
              New Evaluation
            </Button>
          </Box>
        </Box>
      )}

      <APIKeyManager 
        open={apiKeyDialogOpen}
        onClose={() => setApiKeyDialogOpen(false)}
      />
    </Box>
  );
};

export default EvaluationPage;