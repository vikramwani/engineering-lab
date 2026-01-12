"""Agent Alignment UI Backend.

FastAPI backend for the Agent Alignment UI, providing REST API and WebSocket
endpoints for visualization and interaction with the Agent Alignment Framework.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

# Add agent-alignment-framework to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../agent-alignment-framework'))

from agent_alignment import (
    MultiAgentEvaluator,
    EvaluationTask,
    AgentRole,
    BooleanDecisionSchema,
    CategoricalDecisionSchema,
    ScalarDecisionSchema,
    FreeFormDecisionSchema,
    LLMClient,
)
from agent_alignment.core.resolution import AlignmentThresholds
from agent_alignment.llm.providers import OpenAIProvider, AnthropicProvider

# Import the compatibility evaluator
from examples.compatibility.evaluator import CompatibilityEvaluator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agent Alignment UI API",
    description="REST API and WebSocket interface for Agent Alignment Framework visualization",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (React build)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Pydantic models for API
class ProductModel(BaseModel):
    """Product model for compatibility evaluation."""
    id: str
    title: str
    category: str
    brand: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class EvaluationRequest(BaseModel):
    """Request model for evaluation."""
    task_id: Optional[str] = None
    task_type: str
    decision_schema_type: str  # "boolean", "categorical", "scalar", "freeform"
    decision_schema_config: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any]
    evaluation_criteria: str
    agent_roles: Optional[List[Dict[str, Any]]] = None
    alignment_thresholds: Optional[Dict[str, float]] = None
    llm_provider: str = "openai"  # "openai", "anthropic"


class CompatibilityEvaluationRequest(BaseModel):
    """Simplified request model for compatibility evaluation."""
    product_a: ProductModel
    product_b: ProductModel
    task_id: Optional[str] = None


class HITLReviewRequest(BaseModel):
    """Request model for HITL review submission."""
    decision_value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    reviewer_id: str
    evidence: List[str] = Field(default_factory=list)


class APIKeyRequest(BaseModel):
    """Request model for API key configuration."""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None


class APIKeyResponse(BaseModel):
    """Response model for API key status."""
    openai_configured: bool
    anthropic_configured: bool
    openai_key_preview: Optional[str] = None
    anthropic_key_preview: Optional[str] = None


# Global state for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to WebSocket: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection)


manager = ConnectionManager()

# In-memory storage for demo purposes (use database in production)
evaluations_store: Dict[str, Dict[str, Any]] = {}
hitl_requests_store: Dict[str, Dict[str, Any]] = {}

# API key storage (in production, use secure storage)
# Load from shared .env file at startup
api_keys_store = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
    "xai_api_key": os.getenv("XAI_API_KEY"),  # For future XAI support
}


def mask_api_key(api_key: Optional[str]) -> Optional[str]:
    """Mask API key for display purposes."""
    if not api_key:
        return None
    if len(api_key) <= 8:
        return api_key
    return f"{api_key[:4]}...{api_key[-4:]}"


def create_llm_client(provider: str = "openai") -> LLMClient:
    """Create LLM client based on provider."""
    if provider == "openai":
        api_key = api_keys_store.get("openai_api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY is required but not configured")
        
        provider_instance = OpenAIProvider(
            api_key=api_key,
            model="gpt-4o-mini",
        )
    elif provider == "anthropic":
        api_key = api_keys_store.get("anthropic_api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY is required but not configured")
        
        provider_instance = AnthropicProvider(
            api_key=api_key,
            model="claude-3-haiku-20240307",
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported LLM provider: {provider}")
    
    return LLMClient(
        provider=provider_instance,
        max_retries=3,
        timeout_seconds=30,
    )


def create_decision_schema(schema_type: str, config: Dict[str, Any]):
    """Create decision schema based on type and configuration."""
    if schema_type == "boolean":
        return BooleanDecisionSchema(
            positive_label=config.get("positive_label", "positive"),
            negative_label=config.get("negative_label", "negative"),
        )
    elif schema_type == "categorical":
        categories = config.get("categories", ["option_a", "option_b"])
        return CategoricalDecisionSchema(
            categories=categories,
            allow_multiple=config.get("allow_multiple", False),
        )
    elif schema_type == "scalar":
        return ScalarDecisionSchema(
            min_value=config.get("min_value", 0.0),
            max_value=config.get("max_value", 1.0),
        )
    elif schema_type == "freeform":
        return FreeFormDecisionSchema(
            max_length=config.get("max_length"),
            min_length=config.get("min_length"),
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported decision schema type: {schema_type}")


# API Routes

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Agent Alignment UI API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/config/keys", response_model=APIKeyResponse)
async def get_api_keys():
    """Get API key configuration status."""
    return APIKeyResponse(
        openai_configured=bool(api_keys_store.get("openai_api_key")),
        anthropic_configured=bool(api_keys_store.get("anthropic_api_key")),
        openai_key_preview=mask_api_key(api_keys_store.get("openai_api_key")),
        anthropic_key_preview=mask_api_key(api_keys_store.get("anthropic_api_key")),
    )


@app.post("/api/config/keys")
async def update_api_keys(request: APIKeyRequest):
    """Update API key configuration."""
    updated_keys = []
    
    if request.openai_api_key is not None:
        if request.openai_api_key.strip():
            api_keys_store["openai_api_key"] = request.openai_api_key.strip()
            updated_keys.append("OpenAI")
        else:
            api_keys_store["openai_api_key"] = None
            updated_keys.append("OpenAI (cleared)")
    
    if request.anthropic_api_key is not None:
        if request.anthropic_api_key.strip():
            api_keys_store["anthropic_api_key"] = request.anthropic_api_key.strip()
            updated_keys.append("Anthropic")
        else:
            api_keys_store["anthropic_api_key"] = None
            updated_keys.append("Anthropic (cleared)")
    
    return {
        "message": f"Updated API keys: {', '.join(updated_keys)}" if updated_keys else "No keys updated",
        "updated_keys": updated_keys,
        "status": await get_api_keys()
    }


@app.post("/api/evaluations")
async def create_evaluation(request: EvaluationRequest):
    """Create and run a new evaluation."""
    try:
        # Generate task ID if not provided
        task_id = request.task_id or f"eval-{uuid.uuid4().hex[:8]}"
        
        # Create LLM client
        llm_client = create_llm_client(request.llm_provider)
        
        # Create decision schema
        decision_schema = create_decision_schema(
            request.decision_schema_type,
            request.decision_schema_config
        )
        
        # Create evaluation task
        task = EvaluationTask(
            task_id=task_id,
            task_type=request.task_type,
            decision_schema=decision_schema,
            context=request.context,
            evaluation_criteria=request.evaluation_criteria,
        )
        
        # Create agent roles (use defaults if not provided)
        if request.agent_roles:
            agent_roles = [
                AgentRole(**role_config) for role_config in request.agent_roles
            ]
        else:
            # Default agent roles
            agent_roles = [
                AgentRole(
                    name="advocate_agent",
                    role_type="advocate",
                    instruction="Analyze the task and argue FOR the positive outcome.",
                    max_tokens=500,
                    temperature=0.1,
                ),
                AgentRole(
                    name="skeptic_agent",
                    role_type="skeptic",
                    instruction="Analyze the task and argue AGAINST the positive outcome.",
                    max_tokens=500,
                    temperature=0.1,
                ),
                AgentRole(
                    name="judge_agent",
                    role_type="judge",
                    instruction="Review both perspectives and make a final decision.",
                    max_tokens=600,
                    temperature=0.05,
                ),
            ]
        
        # Create alignment thresholds
        alignment_thresholds = None
        if request.alignment_thresholds:
            alignment_thresholds = AlignmentThresholds(**request.alignment_thresholds)
        
        # Create evaluator
        evaluator = MultiAgentEvaluator.from_roles(
            roles=agent_roles,
            llm_client=llm_client,
            alignment_thresholds=alignment_thresholds,
        )
        
        # Broadcast evaluation start
        await manager.broadcast({
            "type": "evaluation_started",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Run evaluation
        result = evaluator.evaluate(task)
        
        # Convert result to serializable format
        evaluation_result = {
            "task_id": result.task_id,
            "task_type": request.task_type,
            "synthesized_decision": result.synthesized_decision,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "evidence": result.evidence,
            "agent_decisions": [
                {
                    "agent_name": decision.agent_name,
                    "role_type": decision.role_type,
                    "decision_value": decision.decision_value,
                    "confidence": decision.confidence,
                    "rationale": decision.rationale,
                    "evidence": decision.evidence,
                    "metadata": decision.metadata,
                }
                for decision in result.agent_decisions
            ],
            "alignment_summary": {
                "state": result.alignment_summary.state.value,
                "alignment_score": result.alignment_summary.alignment_score,
                "decision_agreement": result.alignment_summary.decision_agreement,
                "confidence_spread": result.alignment_summary.confidence_spread,
                "confidence_distribution": result.alignment_summary.confidence_distribution,
                "avg_confidence": result.alignment_summary.avg_confidence,
                "dissenting_agents": result.alignment_summary.dissenting_agents,
                "disagreement_areas": result.alignment_summary.disagreement_areas,
                "consensus_strength": result.alignment_summary.consensus_strength,
                "resolution_rationale": result.alignment_summary.resolution_rationale,
            },
            "requires_human_review": result.requires_human_review,
            "review_reason": result.review_reason,
            "request_id": result.request_id,
            "processing_time_ms": result.processing_time_ms,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Store evaluation result
        evaluations_store[task_id] = evaluation_result
        
        # Create HITL request if needed
        if result.requires_human_review:
            hitl_request = evaluator.create_hitl_request(result)
            if hitl_request:
                hitl_data = {
                    "request_id": hitl_request.request_id,
                    "task_id": hitl_request.task_id,
                    "alignment_state": hitl_request.alignment_state,
                    "alignment_score": hitl_request.alignment_score,
                    "escalation_reason": hitl_request.escalation_reason.value,
                    "summary": hitl_request.summary,
                    "agent_decisions": [
                        {
                            "agent_name": decision.agent_name,
                            "role_type": decision.role_type,
                            "decision_value": decision.decision_value,
                            "confidence": decision.confidence,
                            "rationale": decision.rationale,
                            "evidence": decision.evidence,
                        }
                        for decision in hitl_request.agent_decisions
                    ],
                    "dissenting_agents": hitl_request.dissenting_agents,
                    "created_at": hitl_request.created_at.isoformat(),
                    "metadata": hitl_request.metadata,
                    "status": "pending",
                }
                hitl_requests_store[hitl_request.request_id] = hitl_data
                evaluation_result["hitl_request"] = hitl_data
        
        # Broadcast evaluation completion
        await manager.broadcast({
            "type": "evaluation_completed",
            "task_id": task_id,
            "result": evaluation_result,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        return evaluation_result
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        
        # Broadcast evaluation error
        await manager.broadcast({
            "type": "evaluation_error",
            "task_id": request.task_id or "unknown",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.post("/api/evaluations/compatibility")
async def evaluate_compatibility(request: CompatibilityEvaluationRequest):
    """Simplified endpoint for product compatibility evaluation."""
    try:
        # Create LLM client
        llm_client = create_llm_client("openai")  # Default to OpenAI for compatibility
        
        # Create compatibility evaluator
        evaluator = CompatibilityEvaluator(llm_client=llm_client)
        
        # Run evaluation
        result = evaluator.evaluate_compatibility(
            product_a=request.product_a.dict(),
            product_b=request.product_b.dict(),
            task_id=request.task_id,
        )
        
        # Store evaluation result
        task_id = result.get("request_id", request.task_id or f"compat-{uuid.uuid4().hex[:8]}")
        evaluations_store[task_id] = {
            **result,
            "task_id": task_id,
            "task_type": "product_compatibility",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Broadcast evaluation completion
        await manager.broadcast({
            "type": "evaluation_completed",
            "task_id": task_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Compatibility evaluation failed: {e}", exc_info=True)
        
        # Broadcast evaluation error
        await manager.broadcast({
            "type": "evaluation_error",
            "task_id": request.task_id or "unknown",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.get("/api/evaluations")
async def list_evaluations():
    """List all evaluations."""
    return {
        "evaluations": list(evaluations_store.values()),
        "total": len(evaluations_store),
    }


@app.get("/api/evaluations/{task_id}")
async def get_evaluation(task_id: str):
    """Get specific evaluation by task ID."""
    if task_id not in evaluations_store:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    return evaluations_store[task_id]


@app.delete("/api/evaluations/{task_id}")
async def delete_evaluation(task_id: str):
    """Delete specific evaluation by task ID."""
    if task_id not in evaluations_store:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    deleted_evaluation = evaluations_store.pop(task_id)
    
    # Broadcast evaluation deletion
    await manager.broadcast({
        "type": "evaluation_deleted",
        "task_id": task_id,
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return {"message": f"Evaluation {task_id} deleted successfully", "deleted": deleted_evaluation}


@app.delete("/api/evaluations")
async def clear_all_evaluations():
    """Clear all evaluation history."""
    count = len(evaluations_store)
    evaluations_store.clear()
    
    # Broadcast history cleared
    await manager.broadcast({
        "type": "evaluations_cleared",
        "count": count,
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return {"message": f"Cleared {count} evaluations", "count": count}


@app.get("/api/hitl/requests")
async def list_hitl_requests():
    """List all HITL requests."""
    return {
        "requests": list(hitl_requests_store.values()),
        "total": len(hitl_requests_store),
    }


@app.get("/api/hitl/requests/{request_id}")
async def get_hitl_request(request_id: str):
    """Get specific HITL request."""
    if request_id not in hitl_requests_store:
        raise HTTPException(status_code=404, detail="HITL request not found")
    
    return hitl_requests_store[request_id]


@app.delete("/api/hitl/requests/{request_id}")
async def delete_hitl_request(request_id: str):
    """Delete specific HITL request."""
    if request_id not in hitl_requests_store:
        raise HTTPException(status_code=404, detail="HITL request not found")
    
    deleted_request = hitl_requests_store.pop(request_id)
    
    # Broadcast HITL request deletion
    await manager.broadcast({
        "type": "hitl_request_deleted",
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return {"message": f"HITL request {request_id} deleted successfully", "deleted": deleted_request}


@app.delete("/api/hitl/requests")
async def clear_all_hitl_requests():
    """Clear all HITL requests."""
    count = len(hitl_requests_store)
    hitl_requests_store.clear()
    
    # Broadcast HITL requests cleared
    await manager.broadcast({
        "type": "hitl_requests_cleared",
        "count": count,
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return {"message": f"Cleared {count} HITL requests", "count": count}


@app.post("/api/hitl/requests/{request_id}/review")
async def submit_hitl_review(request_id: str, review: HITLReviewRequest):
    """Submit human review for HITL request."""
    if request_id not in hitl_requests_store:
        raise HTTPException(status_code=404, detail="HITL request not found")
    
    # Update HITL request with review
    hitl_request = hitl_requests_store[request_id]
    hitl_request["status"] = "reviewed"
    hitl_request["review"] = {
        "decision_value": review.decision_value,
        "confidence": review.confidence,
        "rationale": review.rationale,
        "reviewer_id": review.reviewer_id,
        "evidence": review.evidence,
        "reviewed_at": datetime.utcnow().isoformat(),
    }
    
    # Broadcast review completion
    await manager.broadcast({
        "type": "hitl_review_completed",
        "request_id": request_id,
        "review": hitl_request["review"],
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return {"message": "Review submitted successfully", "request": hitl_request}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client messages (ping, subscription requests, etc.)
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat(),
                }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)