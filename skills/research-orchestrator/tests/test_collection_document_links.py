"""Collection tests for document links discovered during web crawling."""
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CRAWL_SCRIPT = ROOT / "skills" / "research-collect" / "scripts" / "parallel_crawl.py"
DOCLING_SCRIPT = ROOT / "skills" / "research-collect" / "scripts" / "parallel_docling.py"


def load_parallel_crawl():
    spec = importlib.util.spec_from_file_location("parallel_crawl", CRAWL_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_parallel_docling():
    spec = importlib.util.spec_from_file_location("parallel_docling", DOCLING_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_crawl_record_exposes_pdf_links_for_docling_queue():
    parallel_crawl = load_parallel_crawl()
    record = {
        "url": "https://docs.cardano.org/about-cardano/explore-more/relevant-research-papers",
        "final_url": "https://docs.cardano.org/about-cardano/explore-more/relevant-research-papers",
        "markdown": (
            "[Ouroboros paper](https://example.com/ouroboros.pdf)\n"
            "[Relative spec](/specs/cardano-ledger.pdf)\n"
            "[HTML page](https://example.com/not-a-document)"
        ),
        "links": {
            "internal": ["/about-cardano/guide", "/papers/hydra.pdf?download=1"],
            "external": ["https://example.org/spec.docx#page=2"],
        },
    }

    assert set(parallel_crawl.document_links_from_record(record)) == {
        "https://example.com/ouroboros.pdf",
        "https://docs.cardano.org/specs/cardano-ledger.pdf",
        "https://docs.cardano.org/papers/hydra.pdf?download=1",
        "https://example.org/spec.docx#page=2",
    }


def test_cardano_iog_pdf_endpoint_is_queued_for_docling():
    parallel_crawl = load_parallel_crawl()
    record = {
        "url": "https://docs.cardano.org/about-cardano/explore-more/relevant-research-papers",
        "final_url": "https://www.iog.io/papers/formal-specification-for-a-cardano-wallet",
        "markdown": "[View/download PDF](https://www.iog.io/api/research/pdf/NRWXWEYR)",
        "links": {"internal": [], "external": []},
    }

    assert parallel_crawl.document_links_from_record(record) == [
        "https://www.iog.io/api/research/pdf/NRWXWEYR"
    ]


def test_cardano_iog_pdf_endpoint_routes_to_docling_sdk():
    parallel_docling = load_parallel_docling()

    assert parallel_docling._routing("https://www.iog.io/api/research/pdf/NRWXWEYR") == (
        "docling_sdk",
        "pdf_url_path",
    )
