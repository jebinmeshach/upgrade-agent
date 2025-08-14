```mermaid
flowchart TD
    A([Start / Trigger]) --> B[Scan Project with Snyk]
    B --> C[Identify Vulnerable Dependencies]
    C --> D[Create OpenRewrite Recipe:<br/>- Java 21 Upgrade<br/>- Spring Boot 3.5 Upgrade<br/>- Snyk Dependency Fixes]
    D --> E[Update pom.xml to Include OpenRewrite Dependency/Plugin]
    E --> F[Run mvn rewrite:run with Created Recipe]
    F --> G[Compile, Build, and Run Unit Tests]
    G -->|Tests Pass| H[Create Pull Request]
    G -->|Tests Fail| I[Fix Failing Test Cases<br/>(LLM or Rewrite Refactor)]
    I --> G
    H --> J([End])
