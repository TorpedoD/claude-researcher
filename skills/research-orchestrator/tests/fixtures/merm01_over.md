# Test Fixture — MERM-01 over limit

## Section with Oversized Mermaid

This section has a mermaid diagram with 16 nodes.

<!-- mermaid: 16 nodes -->
```mermaid
flowchart LR
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    L --> M
    M --> N
    N --> O
    O --> P
```

## Section with Missing Comment

This section has a mermaid diagram with no preceding node count comment.

```mermaid
flowchart TD
    X --> Y
    Y --> Z
```
