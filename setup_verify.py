"""
Quick Start Guide
Run this script to verify your setup
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_environment():
    """Check if environment is properly configured"""
    print("\n" + "="*70)
    print("ENVIRONMENT VERIFICATION")
    print("="*70)
    
    # Check Python version
    print(f"\n✓ Python Version: {sys.version.split()[0]}")
    
    # Check required packages
    required_packages = {
        'langchain': 'LangChain',
        'chromadb': 'ChromaDB',
        'sentence_transformers': 'Sentence Transformers',
        'openai': 'OpenAI',
        'torch': 'PyTorch'
    }
    
    print("\nRequired Packages:")
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - MISSING")
            print(f"    Install with: pip install {package}")
    
    # Check directories
    print("\nProject Structure:")
    dirs_to_check = ['src', 'docs', 'sample_data', 'tests']
    for dir_name in dirs_to_check:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✓ {dir_name}/")
        else:
            print(f"  ✗ {dir_name}/ - MISSING")
    
    # Check files
    print("\nKey Files:")
    files_to_check = {
        'main.py': 'Main entry point',
        'requirements.txt': 'Dependencies',
        'README.md': 'Documentation',
        'src/config.py': 'Configuration',
        'docs/HLD.md': 'High-Level Design',
        'docs/LLD.md': 'Low-Level Design',
        'docs/Technical_Documentation.md': 'Technical Docs'
    }
    
    for file_path, description in files_to_check.items():
        if Path(file_path).exists():
            print(f"  ✓ {file_path} ({description})")
        else:
            print(f"  ✗ {file_path} - MISSING")
    
    print("\n" + "="*70)


def test_imports():
    """Test if core modules can be imported"""
    print("\n" + "="*70)
    print("MODULE IMPORT TEST")
    print("="*70)
    
    modules_to_test = [
        ('config', 'Configuration'),
        ('document_loader', 'Document Loader'),
        ('chunker', 'Document Chunker'),
        ('embeddings', 'Embeddings'),
        ('vector_store', 'Vector Store'),
        ('retriever', 'Retriever'),
        ('rag_engine', 'RAG Engine'),
        ('langgraph_workflow', 'LangGraph Workflow'),
        ('hitl_module', 'HITL Module'),
    ]
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✓ {description} ({module_name}.py)")
        except Exception as e:
            print(f"  ✗ {description} ({module_name}.py)")
            print(f"    Error: {str(e)[:60]}")


def check_openai_key():
    """Check if OpenAI API key is configured"""
    print("\n" + "="*70)
    print("OPENAI API KEY CHECK")
    print("="*70)
    
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key:
        masked_key = api_key[:10] + "..." + api_key[-10:]
        print(f"\n✓ OpenAI API Key configured: {masked_key}")
    else:
        print("\n✗ OpenAI API Key NOT configured")
        print("\nTo configure:")
        print("  Linux/Mac:")
        print("    export OPENAI_API_KEY='your-api-key'")
        print("\n  Windows (PowerShell):")
        print("    $env:OPENAI_API_KEY='your-api-key'")
        print("\n  Or create .env file and use python-dotenv")


def main():
    """Run all checks"""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "RAG CUSTOMER SUPPORT ASSISTANT - SETUP VERIFICATION".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")
    
    check_environment()
    test_imports()
    check_openai_key()
    
    print("\n" + "="*70)
    print("QUICK START GUIDE")
    print("="*70)
    print("""
1. Set OpenAI API Key:
   export OPENAI_API_KEY='your-api-key-here'

2. Run Tests:
   python tests/test_system.py

3. Interactive Mode:
   python main.py --mode interactive

4. Demo Mode:
   python main.py --mode demo

5. Read Documentation:
   - HLD: docs/HLD.md
   - LLD: docs/LLD.md
   - Technical: docs/Technical_Documentation.md

For more help, see README.md
""")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
