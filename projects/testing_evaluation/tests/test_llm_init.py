"""
Test LLM initialization in answering agent
"""
import sys
import os

# Add the projects/slm_orchestration_legal_rag directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
slm_project_path = os.path.join(project_root, 'projects', 'slm_orchestration_legal_rag')
sys.path.insert(0, slm_project_path)

print("=" * 60)
print("Testing LLM Initialization")
print("=" * 60)

# Check imports
print("\n1. Checking imports...")
try:
    from langchain_groq import ChatGroq
    print("   [SUCCESS] langchain_groq imported")
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"   [ERROR] langchain_groq not available: {e}")
    LANGCHAIN_AVAILABLE = False

# Check config
print("\n2. Checking config...")
try:
    from config import config
    groq_key = config.api.GROQ_API_KEY
    print(f"   GROQ_API_KEY: {'[SET]' if groq_key else '[NOT SET]'}")
    print(f"   Key length: {len(groq_key) if groq_key else 0}")
    print(f"   Key starts with: {groq_key[:10] if groq_key else 'N/A'}...")
except Exception as e:
    print(f"   [ERROR] Config error: {e}")

# Test LLM initialization
print("\n3. Testing LLM initialization...")
if LANGCHAIN_AVAILABLE and groq_key:
    try:
        llm = ChatGroq(
            api_key=groq_key,
            model_name="llama3-8b-8192",
            temperature=0.1
        )
        print("   [SUCCESS] LLM initialized!")
        
        # Test a simple call
        print("\n4. Testing LLM call...")
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content="Say hello")])
        print(f"   [SUCCESS] LLM responded: {response.content[:50]}...")
    except Exception as e:
        print(f"   [ERROR] LLM initialization failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   [SKIP] Cannot test - missing dependencies or API key")

# Test answering agent
print("\n5. Testing AnsweringAgent initialization...")
try:
    from answering_agent import AnsweringAgent
    agent = AnsweringAgent()
    print(f"   LLM initialized: {agent.llm is not None}")
    if agent.llm is None:
        print("   [WARNING] LLM is None - will use fallback mode!")
        print("   This is why you see 'direct answer' messages")
    else:
        print("   [SUCCESS] LLM is initialized - should work properly")
except Exception as e:
    print(f"   [ERROR] AnsweringAgent initialization failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)



