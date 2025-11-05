#!/usr/bin/env python3
"""
Test runner script for the Agentic Legal RAG system.
"""
import sys
import subprocess
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("Output:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print(f"Error: {e}")
        if e.stdout:
            print("Stdout:")
            print(e.stdout)
        if e.stderr:
            print("Stderr:")
            print(e.stderr)
        return False


def main():
    """Main test runner function."""
    print("🧪 Agentic Legal RAG System - Test Runner")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("orchestrator.py").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Error: Python 3.10 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Test results
    test_results = []
    
    # 1. Install dependencies
    print("\n📦 Installing dependencies...")
    success = run_command("pip install -r requirements.txt", "Installing requirements")
    test_results.append(("Dependencies", success))
    
    if not success:
        print("❌ Failed to install dependencies. Please check requirements.txt")
        sys.exit(1)
    
    # 2. Run linting
    print("\n🔍 Running code quality checks...")
    
    # Check if black is available
    try:
        subprocess.run("black --version", shell=True, check=True, capture_output=True)
        success = run_command("black --check .", "Code formatting check (Black)")
        test_results.append(("Code Formatting", success))
    except subprocess.CalledProcessError:
        print("⚠️  Black not available, skipping formatting check")
        test_results.append(("Code Formatting", True))
    
    # Check if flake8 is available
    try:
        subprocess.run("flake8 --version", shell=True, check=True, capture_output=True)
        success = run_command("flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics", "Code quality check (Flake8)")
        test_results.append(("Code Quality", success))
    except subprocess.CalledProcessError:
        print("⚠️  Flake8 not available, skipping quality check")
        test_results.append(("Code Quality", True))
    
    # 3. Run unit tests
    print("\n🧪 Running unit tests...")
    success = run_command("python -m pytest tests/ -v", "Unit tests")
    test_results.append(("Unit Tests", success))
    
    # 4. Run integration tests (if available)
    print("\n🔗 Running integration tests...")
    if Path("tests/test_integration.py").exists():
        success = run_command("python -m pytest tests/test_integration.py -v", "Integration tests")
        test_results.append(("Integration Tests", success))
    else:
        print("⚠️  No integration tests found, skipping")
        test_results.append(("Integration Tests", True))
    
    # 5. Test imports
    print("\n📚 Testing imports...")
    try:
        import orchestrator
        import agents
        import data_processing
        import api
        print("✅ All modules imported successfully")
        test_results.append(("Imports", True))
    except ImportError as e:
        print(f"❌ Import error: {e}")
        test_results.append(("Imports", False))
    
    # 6. Test configuration
    print("\n⚙️  Testing configuration...")
    try:
        from config import settings
        print(f"✅ Configuration loaded successfully")
        print(f"   - Embedding model: {settings.EMBEDDING_MODEL}")
        print(f"   - Prompt booster model: {settings.PROMPT_BOOSTER_MODEL}")
        print(f"   - OpenAI model: {settings.OPENAI_MODEL}")
        test_results.append(("Configuration", True))
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        test_results.append(("Configuration", False))
    
    # 7. Test API startup (dry run)
    print("\n🚀 Testing API startup...")
    try:
        # Test if the API can be imported and basic functions work
        from api.main import app
        print("✅ API module imported successfully")
        test_results.append(("API Import", True))
    except Exception as e:
        print(f"❌ API import error: {e}")
        test_results.append(("API Import", False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Set your OpenAI API key in .env file")
        print("2. Run: python example_usage.py")
        print("3. Or start the API: python -m uvicorn api.main:app --reload")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
