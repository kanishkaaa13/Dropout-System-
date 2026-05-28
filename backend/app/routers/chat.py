"""
chat.py
-------
Chat router for Ollama LLM integration.

Provides a POST endpoint /api/v1/chat that interfaces with the local Ollama instance
running on http://127.0.0.1:11434 for dynamic AI responses.

IMPORTANT: To allow CORS requests from frontend, run Ollama with:
    OLLAMA_ORIGINS="*" ollama serve
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])

# ── Request/Response Models ───────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message to send to the AI")
    thread_id: Optional[int] = Field(None, description="Thread ID for conversation context")
    role: Optional[str] = Field("student", description="User role for persona customization")

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="AI response text")
    using_ollama: bool = Field(..., description="Whether Ollama was used or fallback")
    status: str = Field(..., description="Status: 'online' or 'offline'")
    model_used: Optional[str] = Field(None, description="Model name used for generation")


# ── System Prompt Guardrails ─────────────────────────────────────────────────────

def get_system_prompt(role: str = "student") -> str:
    """
    Generate system prompt based on user role.
    
    Args:
        role: User role (student, faculty, admin)
    
    Returns:
        System prompt string for Ollama
    """
    if role == "student":
        return """You are an elite, empathetic AI Academic Counselor for a student preparing for the highly competitive JEE exam. 

Your role is to:
- Provide structured, encouraging, and clear guidance
- Use Markdown syntax for bold headers and bullet points
- Answer general conversations naturally
- Seamlessly guide focus back to structural study habits, physics/chemistry/math optimization, or stress management
- Be supportive and motivational while being practical
- Use examples and actionable advice when possible

Keep responses concise but comprehensive. Use formatting like **bold** for emphasis and bullet points for lists."""
    
    elif role == "faculty":
        return """You are an AI Faculty Assistant for educators at a JEE coaching institute.

Your role is to:
- Help faculty with student analytics and performance insights
- Draft parent communications and intervention strategies
- Provide data-driven recommendations for batch management
- Use Markdown syntax for tables, bold headers, and bullet points
- Be professional, concise, and actionable
- Focus on operational efficiency and student success

Keep responses structured with clear sections and actionable insights."""
    
    elif role == "admin":
        return """You are a System Operations & Analytics Bot for JEE Predictor system administrators.

Your role is to:
- Provide system diagnostics and operational insights
- Help with database verification and health monitoring
- Generate anomaly reports and system summaries
- Use Markdown syntax for code blocks, tables, and structured output
- Be technical, precise, and solution-oriented
- Focus on system reliability and performance optimization

Use code blocks for system output and tables for structured data."""
    
    else:
        return """You are a helpful AI assistant for the JEE Dropout Prediction System.

Provide clear, structured responses using Markdown formatting. Be helpful, accurate, and concise."""


# ── Ollama Integration ───────────────────────────────────────────────────────────

import httpx

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
PREFERRED_MODELS = ["deepseek-r1:1.5b", "mistral", "llama3", "gemma"]  # Priority order for model selection


async def get_available_models() -> List[str]:
    """
    Get list of available models from Ollama.
    
    Returns:
        List of model names available locally
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [model.get("name", "") for model in data.get("models", [])]
                logger.info(f"Available Ollama models: {models}")
                return models
            else:
                logger.warning(f"Failed to get models, status: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        return []


async def select_model() -> Optional[str]:
    """
    Select the best available model from preferred list.
    
    Returns:
        Model name or None if no models available
    """
    available_models = await get_available_models()
    
    for preferred in PREFERRED_MODELS:
        # Check if preferred model is available (exact match or starts with)
        for available in available_models:
            if available == preferred or available.startswith(preferred):
                logger.info(f"Selected model: {available}")
                return available
    
    # If no preferred model found, use first available
    if available_models:
        logger.info(f"Using fallback model: {available_models[0]}")
        return available_models[0]
    
    logger.warning("No models available in Ollama")
    return None


async def call_ollama(message: str, system_prompt: str) -> Optional[tuple[str, str]]:
    """
    Call Ollama API for AI response.
    
    Args:
        message: User message
        system_prompt: System prompt for persona
    
    Returns:
        Tuple of (response_string, model_name) or (None, None) if Ollama is unavailable
    """
    try:
        # Select best available model
        model = await select_model()
        if not model:
            logger.error("Ollama connection failed. Reason: No models available")
            return None, None
        
        # Sanitize payload for Ollama API format
        # Use /api/generate for single prompt (simpler, more reliable)
        payload = {
            "model": model,
            "prompt": f"{system_prompt}\n\nUser: {message}\nAssistant:",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 500
            }
        }
        
        logger.info(f"Ollama connection attempt: URL={OLLAMA_BASE_URL}/api/generate, Model={model}")
        logger.info(f"Payload: prompt_length={len(payload['prompt'])}, stream={payload['stream']}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload
            )
            
            logger.info(f"Ollama response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").strip()
                logger.info(f"Ollama response received successfully. Response length: {len(response_text)}")
                return response_text, model
            else:
                logger.error(f"Ollama connection failed. Reason: HTTP {response.status_code} - {response.text}")
                return None, None
                
    except httpx.ConnectError as e:
        logger.error(f"Ollama connection failed. Reason: Connection refused (ECONNREFUSED) - {e}")
        return None, None
    except httpx.TimeoutException as e:
        logger.error(f"Ollama connection failed. Reason: Request timed out - {e}")
        return None, None
    except Exception as e:
        logger.error(f"Ollama connection failed. Reason: Unexpected error - {type(e).__name__}: {e}")
        return None, None


# ── Fallback Responses ───────────────────────────────────────────────────────────

def get_fallback_response(message: str, role: str = "student") -> str:
    """
    Get fallback response when Ollama is unavailable.
    
    Args:
        message: User message
        role: User role
    
    Returns:
        Fallback response string
    """
    lower_message = message.lower()
    
    if role == "student":
        # Chemistry optimization
        if 'chemistry' in lower_message and ('optimize' in lower_message or 'improve' in lower_message):
            return """To optimize your Chemistry score:

**1. Focus on NCERT First**
- Master all NCERT concepts and examples
- 80% of JEE Chemistry comes from NCERT

**2. Organic Chemistry Strategy**
- Learn reaction mechanisms, don't memorize
- Practice named reactions daily
- Use flashcards for functional groups

**3. Physical Chemistry**
- Master formulas and their applications
- Practice numerical problems regularly
- Focus on thermodynamics and equilibrium

**4. Inorganic Chemistry**
- Create summary tables for trends
- Memorize exceptions separately
- Revise daily for 15 minutes

Would you like me to create a specific study plan for any of these areas?"""
        
        # Stress management
        elif 'stress' in lower_message or 'anxiety' in lower_message:
            return """Managing exam stress is crucial for optimal performance. Here are proven strategies:

**1. Physical Well-being**
- Get 7-8 hours of quality sleep
- Exercise for 30 mins daily (even light walks)
- Stay hydrated and eat balanced meals

**2. Mental Techniques**
- Practice deep breathing (4-7-8 technique)
- Try meditation for 10 mins daily
- Break study into 25-min focused sessions (Pomodoro)

**3. Study Management**
- Set realistic daily goals
- Celebrate small achievements
- Take regular breaks to avoid burnout
- Maintain a study journal to track progress

Remember: Some stress is normal and can actually improve performance. The key is managing it effectively.

Would you like specific techniques for any of these areas?"""
        
        # General JEE information
        elif 'what is' in lower_message or 'jee' in lower_message:
            return """JEE (Joint Entrance Examination) is one of India's most competitive engineering entrance exams.

**JEE Overview:**
- **JEE Main**: Conducted by NTA, serves as qualifying exam for JEE Advanced
- **JEE Advanced**: Conducted by IITs, required for admission to IITs
- **Subjects**: Physics, Chemistry, Mathematics (equal weightage)
- **Mode**: Computer-based test (CBT)

**Key Preparation Areas:**
- **Physics**: Mechanics, Electromagnetism, Optics, Modern Physics
- **Chemistry**: Organic, Inorganic, Physical Chemistry
- **Mathematics**: Calculus, Algebra, Coordinate Geometry, Trigonometry

**Success Factors:**
- Consistent daily practice (6-8 hours)
- Strong conceptual understanding
- Regular mock tests and analysis
- Time management during exam
- Physical and mental well-being

Would you like specific strategies for any subject or aspect of JEE preparation?"""
        
        # Rank-related queries
        elif 'rank' in lower_message:
            return """Understanding JEE rank and performance:

**Rank Determination:**
- JEE Main rank is based on normalized scores across multiple sessions
- JEE Advanced rank is based on aggregate marks
- All India Rank (AIR) determines college and branch eligibility

**Target Setting:**
- **Top 100 AIR**: IIT Bombay (Computer Science)
- **Top 1000 AIR**: Top IITs (Computer Science, Electrical)
- **Top 5000 AIR**: IITs (various branches)
- **Top 20000 AIR**: NITs and IIITs (top branches)
- **Top 50000 AIR**: NITs and IIITs (good branches)

**Improvement Strategy:**
- Analyze weak subjects through mock tests
- Focus on high-weightage topics
- Improve speed and accuracy
- Regular revision of formulas and concepts

Use the Prediction Engine to analyze your current metrics and get personalized rank projections.

Would you like help with specific rank improvement strategies?"""
        
        # Physics-related queries
        elif 'physics' in lower_message:
            return """To excel in Physics for JEE:

**Core Topics to Master:**
1. **Mechanics** (Kinematics, Laws of Motion, Work-Energy, Rotational Motion)
2. **Electromagnetism** (Electrostatics, Current Electricity, Magnetism)
3. **Optics** (Ray Optics, Wave Optics)
4. **Modern Physics** (Dual Nature, Atoms, Nuclei)
5. **Thermodynamics** (Laws, Processes, Heat Engines)

**Study Strategy:**
- Focus on understanding concepts, not memorizing formulas
- Practice numerical problems daily (minimum 20-30)
- Solve previous year JEE papers
- Use diagrams and visualizations for better understanding
- Master standard problem-solving techniques

**Common Mistakes to Avoid:**
- Neglecting numerical practice
- Skipping derivations
- Not revising regularly
- Ignoring units and dimensions

Would you like specific strategies for any Physics topic?"""
        
        # Time management
        elif 'time' in lower_message or 'schedule' in lower_message:
            return """Effective time management for JEE preparation:

**Daily Schedule Template:**
- **Morning (6:00-10:00)**: Physics (most alert time)
- **Afternoon (2:00-5:00)**: Mathematics (problem-solving)
- **Evening (6:00-9:00)**: Chemistry (conceptual study)
- **Night (9:30-10:30)**: Revision and planning

**Weekly Structure:**
- **Monday-Thursday**: New topics and practice
- **Friday**: Mock tests and analysis
- **Saturday**: Weak area focus
- **Sunday**: Revision and relaxation

**Time Management Tips:**
- Use Pomodoro technique (25 min study, 5 min break)
- Prioritize high-weightage topics
- Set daily and weekly goals
- Track time spent on each subject
- Include buffer time for unexpected delays

**Avoid Time Wasters:**
- Excessive social media
- Unnecessary phone usage
- Long breaks between study sessions
- Studying too many topics simultaneously

Would you like a personalized schedule based on your current study patterns?"""
        
        # Default fallback for other queries
        else:
            return """I can help you with JEE preparation guidance. Here are some areas I can assist with:

**Subject-Specific Help:**
- Chemistry optimization strategies
- Physics problem-solving techniques
- Mathematics practice plans

**General Preparation:**
- Time management and study schedules
- Stress management techniques
- Rank projection and improvement
- Mock test analysis

**Common Topics:**
- "How to optimize Chemistry score"
- "Tips for managing exam stress"
- "Time management strategies"
- "Physics problem-solving improvement"
- "Rank tracking and targets"

For personalized advice based on your performance metrics, please use the Prediction Engine or connect with your faculty counselor.

What specific aspect of JEE preparation would you like help with?"""
    
    elif role == "faculty":
        return """I can assist with faculty operations and student management:

**Available Capabilities:**
- Draft parent communication templates
- Analyze topic-wise accuracy and performance
- Create assignment schedules
- Monitor attendance trends
- Compare performance across batches
- Generate intervention strategies

**Common Queries:**
- "Draft parent follow-up for at-risk students"
- "Which topic has lowest accuracy in Batch 1?"
- "Generate assignment schedule for Physics"
- "Show students with declining attendance"
- "Compare performance across all batches"

For real-time data and personalized insights, please use the Faculty Dashboard.

What specific faculty operation would you like help with?"""
    
    elif role == "admin":
        return """I can assist with system operations and administration:

**Available Capabilities:**
- Export system anomaly reports
- Check backend service gateway status
- Run diagnostic verification on datasets
- Generate system health summaries
- Verify database integrity
- Monitor system performance

**Common Queries:**
- "Export system anomaly reports"
- "Check backend service gateway status"
- "Run diagnostic verification on datasets"
- "Generate system health summary"
- "Verify database integrity"

For real-time monitoring and system administration, please use the Admin Dashboard.

What specific system operation would you like help with?"""
    
    else:
        return "I can assist with general JEE Dropout Prediction System queries. Please specify your role (student, faculty, admin) for more targeted assistance."


# ── Chat Endpoint ───────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    """
    Chat endpoint that interfaces with Ollama for dynamic AI responses.
    
    Falls back to local keyword-based responses if Ollama is unavailable.
    
    Args:
        request: Chat request with message and optional thread_id
        http_request: FastAPI request object
    
    Returns:
        ChatResponse with AI response and status
    """
    # Get user role from request or default to student
    role = request.role or "student"
    
    # Generate system prompt based on role
    system_prompt = get_system_prompt(role)
    
    # Try to call Ollama
    ollama_response, model_used = await call_ollama(request.message, system_prompt)
    
    if ollama_response:
        logger.info(f"Successfully called Ollama for role={role}, model={model_used}")
        return ChatResponse(
            response=ollama_response,
            using_ollama=True,
            status="online",
            model_used=model_used
        )
    else:
        logger.warning(f"Ollama unavailable, using fallback for role={role}")
        fallback_response = get_fallback_response(request.message, role)
        return ChatResponse(
            response=fallback_response,
            using_ollama=False,
            status="offline",
            model_used=None
        )


@router.get("/chat/status")
async def chat_status() -> dict:
    """
    Check Ollama connection status and available models.
    
    Returns:
        Status dict with Ollama availability and model information
    """
    try:
        # Check if Ollama is running
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [model.get("name", "") for model in models]
                
                # Select best model
                selected_model = await select_model()
                
                return {
                    "ollama_available": True,
                    "status": "online",
                    "models": model_names,
                    "selected_model": selected_model,
                    "model_count": len(models)
                }
            else:
                logger.warning(f"Ollama status check failed: {response.status_code}")
                return {
                    "ollama_available": False,
                    "status": "offline",
                    "error": f"Ollama returned status {response.status_code}"
                }
    except httpx.ConnectError as e:
        logger.error(f"Ollama connection refused during status check: {e}")
        return {
            "ollama_available": False,
            "status": "offline",
            "error": "Connection refused - Ollama may not be running"
        }
    except Exception as e:
        logger.error(f"Unexpected error during Ollama status check: {e}")
        return {
            "ollama_available": False,
            "status": "offline",
            "error": str(e)
        }
