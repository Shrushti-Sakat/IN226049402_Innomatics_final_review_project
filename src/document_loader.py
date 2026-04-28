"""
Document Loader Module
Handles PDF document loading and initial processing
"""

import os
from pathlib import Path
from typing import List
from pypdf import PdfReader
from config import DATA_DIR


class DocumentLoader:
    """Load and preprocess PDF documents"""
    
    def __init__(self, data_dir: Path = DATA_DIR):
        """
        Initialize DocumentLoader
        
        Args:
            data_dir: Directory containing PDF files
        """
        self.data_dir = Path(data_dir)
        self.documents = []
    
    def load_pdfs(self) -> List[dict]:
        """
        Load all PDF files from the data directory
        
        Returns:
            List of documents with content and metadata
        """
        self.documents = []
        
        if not self.data_dir.exists():
            print(f"Warning: Data directory {self.data_dir} does not exist")
            return self.documents
        
        pdf_files = list(self.data_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {self.data_dir}")
            return self.documents
        
        for pdf_path in pdf_files:
            print(f"Loading: {pdf_path.name}")
            try:
                self._load_single_pdf(pdf_path)
            except Exception as e:
                print(f"Error loading {pdf_path.name}: {str(e)}")
        
        print(f"Loaded {len(self.documents)} documents")
        return self.documents
    
    def _load_single_pdf(self, pdf_path: Path) -> None:
        """
        Load a single PDF file and extract text
        
        Args:
            pdf_path: Path to the PDF file
        """
        reader = PdfReader(pdf_path)
        
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()
            
            if text.strip():  # Only add non-empty pages
                self.documents.append({
                    "content": text,
                    "source": pdf_path.name,
                    "page": page_idx + 1,
                    "metadata": {
                        "source_file": str(pdf_path),
                        "page_number": page_idx + 1,
                        "total_pages": len(reader.pages)
                    }
                })
    
    def load_sample_documents(self) -> List[dict]:
        """
        Create sample documents for testing
        
        Returns:
            List of sample documents
        """
        self.documents = [
            {
                "content": """Customer Support Policy

1. Response Time:
   - Urgent issues: Within 1 hour
   - High priority: Within 4 hours
   - Standard: Within 24 hours

2. Escalation Process:
   - Level 1: Basic support
   - Level 2: Technical support
   - Level 3: Senior engineer
   
3. Contact Methods:
   - Email: support@company.com
   - Phone: 1-800-SUPPORT
   - Chat: Available 24/7""",
                "source": "customer_policy.pdf",
                "page": 1,
                "metadata": {"source_file": "customer_policy.pdf", "page_number": 1}
            },
            {
                "content": """Product Features

Our product includes:
- Real-time synchronization across devices
- End-to-end encryption for data security
- Offline mode for continued access
- Cloud backup every 6 hours
- Support for up to 1000 users per account""",
                "source": "product_features.pdf",
                "page": 1,
                "metadata": {"source_file": "product_features.pdf", "page_number": 1}
            },
            {
                "content": """Troubleshooting Guide

Common Issues:
1. Connection problems:
   - Check internet connection
   - Restart the application
   - Clear browser cache

2. Login issues:
   - Reset password using forgot password link
   - Check for caps lock
   - Ensure correct email address
   
3. Data sync issues:
   - Force sync from settings
   - Check device storage
   - Update to latest version""",
                "source": "troubleshooting.pdf",
                "page": 1,
                "metadata": {"source_file": "troubleshooting.pdf", "page_number": 1}
            }
        ]
        return self.documents
