# Provenance and reuse status

The proposed starting point is a local folder supplied by the project owner named `MediBot-main`. Its reviewed files include a FastAPI application, an HTML/CSS interface, Databricks-backed classification and retrieval, and an LLM answer-generation flow.

MediBot is the supplied baseline; WellQuery is its extension. The folder alone does not establish authorship or licensing. No upstream repository URL or license file was supplied. Original authorship should be credited once confirmed; imported components are not presented as newly written WellQuery code.

The application, LLM wrapper, HTML/CSS interface, and original requirements have now been imported from that folder. The initial import is recorded in `docs/medibot-baseline.json`; subsequent changes are WellQuery development. No model artifacts, datasets, or health-document content have been imported from MediBot. External asset URLs in the original UI are part of the baseline and will be removed as the interface is adapted.

When importing code:

1. Identify the imported MediBot baseline and record its repository URL if available.
2. Preserve any third-party license and copyright notices found in dependencies or imported components.
3. Clearly distinguish existing MediBot components from new WellQuery contributions.
4. Check course requirements for the use of prior work and third-party code.

Document-source permissions and attribution will be recorded separately when the knowledge base is selected. Permission to reuse application code does not establish permission to reuse its source documents.

## Restored Databricks foundation

The original Databricks helpers and notebooks are now included, with source hashes in `docs/medibot-databricks-baseline.json`. Changes replace personal workspace paths and clear notebook outputs. The existing FastAPI, Databricks client, Transformers wrapper, and original prompt form the default runtime again. See `docs/ARCHITECTURE.md` for the separately retained local experiments.
