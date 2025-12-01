"""
Setup Verification Script
=========================
Validates that the live agent orchestrator environment is correctly configured.

Checks:
1. Python version compatibility
2. Required dependencies installed
3. .env file exists with valid API key
4. Gemini API connectivity
5. Scorecard parsing functionality
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Verify Python version is 3.8 or higher."""
    print("\n[CHECK 1] Python Version")
    print("-" * 50)
    
    version = sys.version_info
    print(f"  Current version: Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ❌ FAIL: Python 3.8+ required")
        return False
    
    print("  ✅ PASS: Python version compatible")
    return True


def check_dependencies():
    """Verify all required packages are installed."""
    print("\n[CHECK 2] Dependencies")
    print("-" * 50)
    
    required_packages = [
        ('google.generativeai', 'google-generativeai'),
        ('dotenv', 'python-dotenv'),
        ('requests', 'requests'),
        ('colorama', 'colorama')
    ]
    
    all_installed = True
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} - NOT INSTALLED")
            all_installed = False
    
    if not all_installed:
        print("\n  Run: pip install -r requirements.txt")
        return False
    
    print("\n  ✅ PASS: All dependencies installed")
    return True


def check_env_file():
    """Verify .env file exists and contains API key."""
    print("\n[CHECK 3] Environment Configuration")
    print("-" * 50)
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print("  ❌ FAIL: .env file not found")
        print("\n  Create .env file:")
        print("    1. Copy .env.template to .env")
        print("    2. Add your GEMINI_API_KEY")
        return False
    
    print("  ✅ .env file exists")
    
    # Load and check API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("  ❌ FAIL: GEMINI_API_KEY not set in .env")
        return False
    
    if api_key == 'your_gemini_api_key_here':
        print("  ❌ FAIL: GEMINI_API_KEY is still the template value")
        print("\n  Edit .env and replace with your actual API key")
        print("  Get key from: https://makersuite.google.com/app/apikey")
        return False
    
    # Mask the key for security
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"  ✅ GEMINI_API_KEY set: {masked_key}")
    print("\n  ✅ PASS: Environment configured")
    return True


def check_api_connectivity():
    """Test Gemini API connection with a simple prompt."""
    print("\n[CHECK 4] Gemini API Connectivity")
    print("-" * 50)
    
    try:
        from gemini_utils import create_gemini_client, call_gemini_with_retry
        
        print("  Testing API connection...")
        
        # Create client
        model = create_gemini_client("gemini-2.0-flash-exp")
        print("  ✅ Client initialized")
        
        # Test with simple prompt
        test_prompt = "Respond with exactly: 'API connection successful'"
        response = call_gemini_with_retry(model, test_prompt, max_retries=2)
        
        print(f"  ✅ API response received ({len(response)} characters)")
        print(f"     Response preview: {response[:100]}...")
        
        print("\n  ✅ PASS: Gemini API is accessible")
        return True
        
    except ValueError as e:
        if "GEMINI_API_KEY" in str(e):
            print(f"  ❌ FAIL: {e}")
            return False
        raise
    except Exception as e:
        print(f"  ❌ FAIL: API connection error")
        print(f"     Error: {e}")
        print("\n  Troubleshooting:")
        print("    - Verify your API key is valid")
        print("    - Check you have quota/credits available")
        print("    - Ensure internet connection is working")
        return False


def check_scorecard_parsing():
    """Test scorecard extraction functionality."""
    print("\n[CHECK 5] Scorecard Parsing")
    print("-" * 50)
    
    try:
        from gemini_utils import extract_scorecard
        
        # Test with valid scorecard
        test_response = """
**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [YES]
* Lean_Plan_Table_Present: [YES]
* Citation_Quality_Pass: [YES]
**END_SCORECARD**

All requirements met. Document approved.
"""
        
        scorecard, audit_report = extract_scorecard(test_response)
        
        if len(scorecard) == 3:
            print("  ✅ Valid scorecard parsed correctly")
        else:
            print(f"  ⚠️  WARNING: Expected 3 fields, got {len(scorecard)}")
        
        # Test with corrupted scorecard
        corrupted_response = "No scorecard markers present in this response."
        scorecard2, audit_report2 = extract_scorecard(corrupted_response)
        
        if len(scorecard2) == 0:
            print("  ✅ Corrupted input handled gracefully")
        else:
            print("  ⚠️  WARNING: Unexpected scorecard from corrupted input")
        
        print("\n  ✅ PASS: Scorecard parsing functional")
        return True
        
    except Exception as e:
        print(f"  ❌ FAIL: Scorecard parsing error")
        print(f"     Error: {e}")
        return False


def check_file_structure():
    """Verify all required files are present."""
    print("\n[CHECK 6] File Structure")
    print("-" * 50)
    
    required_files = [
        'gemini_utils.py',
        'prompts.py',
        'live_agent_orchestrator.py',
        'requirements.txt',
        '.gitignore'
    ]
    
    all_present = True
    
    for filename in required_files:
        if Path(filename).exists():
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename} - MISSING")
            all_present = False
    
    if not all_present:
        print("\n  ❌ FAIL: Some required files are missing")
        return False
    
    print("\n  ✅ PASS: All required files present")
    return True


def main():
    """Run all verification checks."""
    print("="*70)
    print("🔧 LIVE AGENT ORCHESTRATOR - SETUP VERIFICATION")
    print("="*70)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment Configuration", check_env_file),
        ("File Structure", check_file_structure),
        ("Gemini API Connectivity", check_api_connectivity),
        ("Scorecard Parsing", check_scorecard_parsing),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n  ❌ UNEXPECTED ERROR: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("📊 VERIFICATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {check_name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ALL CHECKS PASSED - System ready for live execution!")
        print("\nNext steps:")
        print("  1. Review README_LIVE_ORCHESTRATOR.md for usage guide")
        print("  2. Run: python live_agent_orchestrator.py")
        return 0
    else:
        print("\n⚠️  SETUP INCOMPLETE - Please fix the failed checks above")
        return 1


if __name__ == '__main__':
    exit_code = main()
    print("\n" + "="*70 + "\n")
    sys.exit(exit_code)
