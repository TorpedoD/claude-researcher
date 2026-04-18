## Overview

This document provides an overview of the research pipeline architecture.
The system collects evidence from multiple sources and synthesizes findings.
Citations are tracked inline for full provenance.

For more information on architectural choices, see [Source](https://example.com/overview).

## Architecture

The pipeline consists of three main stages: collection, synthesis, and formatting.
Each stage operates independently with well-defined interfaces between them.
The collection stage uses Crawl4AI to gather web content into structured markdown.
The synthesis stage uses graphify to build a knowledge graph from collected evidence.

For implementation details, see [Design Doc](https://example.com/design).
For deployment guidance, see [Deployment](https://example.com/deploy).

```python
def run_pipeline(run_dir):
    collect(run_dir)
    synthesize(run_dir)
    format_output(run_dir)
```
