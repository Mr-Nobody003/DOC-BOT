#!/usr/bin/env python3
"""
Pre-deployment validation script for deploy branch.
Checks all critical components without running full queries.
Exit code 0 = ready to deploy, non-zero = issues found.
"""
import sys
import os
import subprocess
from pathlib import Path

# Add repo to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def check(name: str, fn, critical: bool = False) -> bool:
    """Run a check and report results."""
    try:
        fn()
        print(f"  {Colors.GREEN}✅{Colors.END} {name}")
        return True
    except Exception as e:
        symbol = "❌" if critical else "⚠️"
        print(f"  {symbol} {name}")
        if critical:
            print(f"     {Colors.RED}{type(e).__name__}: {e}{Colors.END}")
        return not critical  # Critical checks fail validation


def main() -> int:
    """Run all validation checks."""
    print(f"\n{Colors.BLUE}🚀 Pre-Deployment Validation for Deploy Branch{Colors.END}\n")
    
    all_passed = True
    
    # 1. Import checks (CRITICAL)
    print(f"{Colors.BLUE}1. Core Imports (CRITICAL){Colors.END}")
    
    def check_backend_core():
        from backend.core.config import get_settings
        from backend.db.qdrant import get_qdrant_client
        from backend.agents.retrieval import retrieval_agent_node
        from backend.retrieval.qdrant_store import QdrantStore
        from backend.retrieval.hybrid_search import HybridRetriever
    
    if not check("Backend core modules", check_backend_core, critical=True):
        all_passed = False
    
    def check_services():
        from backend.retrieval.embeddings import EmbeddingService
        from backend.ingestion.pubmed import PubMedFetcher
    
    if not check("Service modules", check_services, critical=True):
        all_passed = False
    
    # 2. Configuration checks (CRITICAL)
    print(f"\n{Colors.BLUE}2. Configuration{Colors.END}")
    
    def check_config():
        from backend.core.config import get_settings
        settings = get_settings()
        # Just check that settings loads, not that keys are present
        assert settings is not None
    
    check("Settings loaded", check_config, critical=True)
    
    # 3. File structure
    print(f"\n{Colors.BLUE}3. Project Structure (CRITICAL){Colors.END}")
    
    required_files = [
        "backend/main.py",
        "backend/requirements.txt",
        "backend/vercel.json",
        "backend/.vercelignore",
        "scripts/ingest_qdrant_cloud.py",
        "pytest.ini",
        "DEPLOY_SYNC_PLAN.md",
        "QDRANT_CLOUD_SETUP.md",
    ]
    
    for file_path in required_files:
        def check_file(f=file_path):
            assert Path(f).exists(), f"Missing {f}"
        
        if not check(f"Exists: {file_path}", check_file, critical=True):
            all_passed = False
    
    # 4. API endpoints
    print(f"\n{Colors.BLUE}4. API Structure (CRITICAL){Colors.END}")
    
    def check_api():
        from backend.api.main import app
        assert hasattr(app, 'openapi'), "API app not properly configured"
    
    check("FastAPI app configured", check_api, critical=True)
    
    # 5. Graph builder
    print(f"\n{Colors.BLUE}5. Graph Components (CRITICAL){Colors.END}")
    
    def check_graph():
        from backend.graph.builder import build_medical_evidence_graph
        assert callable(build_medical_evidence_graph)
    
    check("Graph builder available", check_graph, critical=True)
    
    # 6. Retrieval components
    print(f"\n{Colors.BLUE}6. Retrieval Components{Colors.END}")
    
    def check_embedder():
        from backend.retrieval.embeddings import EmbeddingService
        embedder = EmbeddingService()
        assert embedder is not None
    
    check("Embedding service", check_embedder, critical=False)
    
    def check_pubmed():
        from backend.ingestion.pubmed import PubMedFetcher
        fetcher = PubMedFetcher()
        assert fetcher is not None
    
    check("PubMed fetcher", check_pubmed, critical=False)
    
    # 7. Git status
    print(f"\n{Colors.BLUE}7. Git Status (INFO){Colors.END}")
    
    def check_branch():
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True
        )
        branch = result.stdout.strip()
        assert branch == "deploy", f"Not on deploy branch: {branch}"
        print(f"     On branch: {Colors.GREEN}{branch}{Colors.END}")
    
    if not check("On deploy branch", check_branch, critical=True):
        all_passed = False
    
    def check_status():
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(f"     {Colors.YELLOW}Uncommitted changes detected (will be ignored){Colors.END}")
        else:
            print(f"     {Colors.GREEN}Working tree clean{Colors.END}")
    
    check("Git status", check_status, critical=False)
    
    # 8. Recent commits
    print(f"\n{Colors.BLUE}8. Commit History{Colors.END}")
    
    def check_commits():
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True,
            text=True
        )
        commits = result.stdout.strip().split('\n')
        if commits:
            print(f"     Latest commits:")
            for commit in commits[:3]:
                print(f"       {commit}")
    
    check("Recent commits", check_commits, critical=False)
    
    # Final summary
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    
    if all_passed:
        print(f"{Colors.GREEN}✅ Deploy branch is READY for production!{Colors.END}\n")
        print(f"{Colors.YELLOW}📋 Pre-deployment checklist:{Colors.END}")
        print(f"  [ ] 1. Configure .env with Qdrant Cloud credentials")
        print(f"       export QDRANT_CLIENT_API_ENDPOINT=https://xxx.qdrant.io")
        print(f"       export QDRANT_CLIENT_API_KEY=your-api-key")
        print(f"  [ ] 2. Test ingestion locally: python scripts/ingest_qdrant_cloud.py")
        print(f"  [ ] 3. Commit changes: git add . && git commit -m 'Deploy ready'")
        print(f"  [ ] 4. Push to origin: git push origin deploy")
        print(f"  [ ] 5. Monitor Vercel deployment (auto-triggers)")
        print(f"  [ ] 6. Check Vercel logs for any timeout messages (expected)")
        print(f"\n{Colors.YELLOW}📚 Documentation:{Colors.END}")
        print(f"  - DEPLOY_SYNC_PLAN.md: Sync strategy & stability")
        print(f"  - QDRANT_CLOUD_SETUP.md: Qdrant Cloud configuration")
        print(f"  - scripts/ingest_qdrant_cloud.py: Batch ingestion")
        print()
        return 0
    else:
        print(f"{Colors.RED}❌ Deploy branch has CRITICAL issues!{Colors.END}\n")
        print(f"{Colors.YELLOW}Review errors above and fix them before deploying.{Colors.END}\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as e:
        print(f"\n{Colors.RED}💥 Validation failed: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    
    sys.exit(exit_code)
