# AIID Expert Search
<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
User-confirmed: React, TypeScript, Vite, Tailwind; Django/DRF and PostgreSQL 16 in Docker Compose.

## Users
Confirmed first-screen scope: coordinator workspace, free-text search, optional industry filter, comparison of three experts, no registration. Actual AIID job titles remain a discovery hypothesis.

## Product Purpose
Turn a natural-language task into an evidence-based shortlist from the Alliance registry. A human decides; this is not automated hiring.

## Capabilities and Constraints
Offline runtime; no paid AI APIs. Backend: BM25 + taxonomy, 120 synthetic profiles. Explain matches, missing requirements, unrecognized words and availability. Percent is recognized requirement coverage, not probability. Almas owns local Qwen integration; baseline must run without it. Do not fabricate contacts, qualifications, usage metrics or feedback persistence.

## Evidence on Hand
docs/API_CONTRACT.md, docs/discovery/, data/experts.csv. User delegated visual and interaction details. No official brand assets or real expert portraits supplied.
