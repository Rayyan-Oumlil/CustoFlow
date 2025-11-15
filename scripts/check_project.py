"""
Project Verification Script
Checks that all essential components are present and functional before submission.
"""
import os
import sys
from pathlib import Path

# Colors for output (using ASCII-safe characters)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    exists = Path(filepath).exists()
    status = f"{GREEN}[OK]{RESET}" if exists else f"{RED}[MISSING]{RESET}"
    print(f"  {status} {description}: {filepath}")
    return exists

def check_directory_exists(dirpath: str, description: str) -> bool:
    """Check if a directory exists."""
    exists = Path(dirpath).is_dir()
    status = f"{GREEN}[OK]{RESET}" if exists else f"{RED}[MISSING]{RESET}"
    print(f"  {status} {description}: {dirpath}")
    return exists

def check_import(module_name: str, description: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        print(f"  {GREEN}[OK]{RESET} {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"  {RED}[FAIL]{RESET} {description}: {module_name} - {e}")
        return False

def main():
    """Run project verification checks."""
    print("=" * 70)
    print(f"{BLUE}CustoFlow - Project Verification{RESET}")
    print("=" * 70)
    print()
    
    checks_passed = 0
    checks_total = 0
    
    # Essential files
    print(f"{YELLOW}Essential Files:{RESET}")
    essential_files = [
        ("README.md", "Main documentation"),
        ("requirements.txt", "Dependencies"),
        ("main.py", "CLI entry point"),
        (".env", "Environment configuration"),
        ("LICENSE", "License file"),
    ]
    
    for filepath, desc in essential_files:
        checks_total += 1
        if check_file_exists(filepath, desc):
            checks_passed += 1
    print()
    
    # Core directories
    print(f"{YELLOW}Core Directories:{RESET}")
    core_dirs = [
        ("agents", "Agent definitions"),
        ("tools", "Custom tools"),
        ("tests", "Test suite"),
        ("api", "API server"),
        ("docs", "Documentation"),
        ("utils", "Utilities"),
        ("memory", "Memory management"),
        ("observability", "Observability"),
        ("config", "Configuration"),
    ]
    
    for dirpath, desc in core_dirs:
        checks_total += 1
        if check_directory_exists(dirpath, desc):
            checks_passed += 1
    print()
    
    # Key agent files
    print(f"{YELLOW}Agent Files:{RESET}")
    agent_files = [
        ("agents/orchestrator_agent.py", "Orchestrator agent"),
        ("agents/faq_agent.py", "FAQ agent"),
        ("agents/order_agent.py", "Order agent"),
        ("agents/sentiment_agent.py", "Sentiment agent"),
        ("agents/escalation_agent.py", "Escalation agent"),
    ]
    
    for filepath, desc in agent_files:
        checks_total += 1
        if check_file_exists(filepath, desc):
            checks_passed += 1
    print()
    
    # Key tool files
    print(f"{YELLOW}Tool Files:{RESET}")
    tool_files = [
        ("tools/faq_tool.py", "FAQ tool"),
        ("tools/order_tool.py", "Order tool"),
        ("tools/ticket_tool.py", "Ticket tool"),
        ("tools/ticket_tool_lro.py", "LRO tool"),
    ]
    
    for filepath, desc in tool_files:
        checks_total += 1
        if check_file_exists(filepath, desc):
            checks_passed += 1
    print()
    
    # Documentation files
    print(f"{YELLOW}Documentation:{RESET}")
    doc_files = [
        ("docs/API.md", "API documentation"),
        ("docs/SETUP.md", "Setup guide"),
        ("docs/TROUBLESHOOTING.md", "Troubleshooting guide"),
        ("docs/ADVANCED_EXAMPLES.md", "Advanced examples"),
    ]
    
    for filepath, desc in doc_files:
        checks_total += 1
        if check_file_exists(filepath, desc):
            checks_passed += 1
    print()
    
    # Test files
    print(f"{YELLOW}Test Files:{RESET}")
    test_files = [
        ("tests/test_faq_agent.py", "FAQ agent tests"),
        ("tests/test_order_agent.py", "Order agent tests"),
        ("tests/test_orchestrator_agent.py", "Orchestrator tests"),
        ("tests/test_sentiment_agent.py", "Sentiment tests"),
        ("tests/test_escalation_agent.py", "Escalation tests"),
        ("tests/test_integration.py", "Integration tests"),
        ("tests/test_security.py", "Security tests"),
        ("notebooks/evaluation.py", "Evaluation suite"),
    ]
    
    for filepath, desc in test_files:
        checks_total += 1
        if check_file_exists(filepath, desc):
            checks_passed += 1
    print()
    
    # Check imports (basic syntax check)
    print(f"{YELLOW}Import Checks:{RESET}")
    import_checks = [
        ("agents.orchestrator_agent", "Orchestrator agent import"),
        ("agents.faq_agent", "FAQ agent import"),
        ("agents.order_agent", "Order agent import"),
        ("tools.faq_tool", "FAQ tool import"),
        ("tools.order_tool", "Order tool import"),
        ("api.server", "API server import"),
    ]
    
    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    for module, desc in import_checks:
        checks_total += 1
        if check_import(module, desc):
            checks_passed += 1
    print()
    
    # Summary
    print("=" * 70)
    print(f"{BLUE}Verification Summary:{RESET}")
    print("=" * 70)
    percentage = (checks_passed / checks_total * 100) if checks_total > 0 else 0
    print(f"Checks passed: {GREEN}{checks_passed}/{checks_total}{RESET} ({percentage:.1f}%)")
    
    if checks_passed == checks_total:
        print(f"\n{GREEN}[SUCCESS] All checks passed! Project is ready for submission.{RESET}")
        return 0
    else:
        print(f"\n{YELLOW}[WARNING] Some checks failed. Please review the issues above.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

