# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Primary:** SST (Seguridad y Salud en el Trabajo) coordinator at a company that is preparing or maintaining ISO 45001 documentation.

They work with policies, procedures, risk matrices, training records, and audit reports scattered across folders, email, and shared drives. Their job is to classify, organize, and trace documents against normative categories so the organization can demonstrate compliance and find the right artifact quickly during audits or internal reviews.

**Other audiences (secondary, not primary design target):** quality/compliance managers spanning multiple ISO standards; external consultants — may use the same flows but are not the default persona.

## Product Purpose

TechISOlutions helps organizations organize and automatically classify technical documents against **ISO 45001** (Seguridad y Salud en el Trabajo) requirements. Users submit document text or upload files; machine-learning models assign a normative document category, extract keywords, surface related content, and persist results for search and dashboard review.

Success means a coordinator can ingest a batch of mixed documentation, see consistent ISO-aligned categories and keywords, upload supporting files to cloud storage, and retrieve or search classified content without manual tagging — demonstrated end-to-end in the hackathon demo flow (register → login → classify → upload → search → dashboard).

Future scope (not current sprint commitment): ISO 9001 (Calidad) and ISO 14001 (Medio Ambiente).

## Positioning

Classification is trained and scoped to **ISO 45001 document types** (e.g. Política SST, Procedimientos, Matrices de Riesgo, Registros, Auditorías) — not a generic document management system. The differentiator is normative-aware ML classification plus keyword extraction and similarity, exposed through a full stack (Next.js UI, Spring Boot API, Python ML service, Supabase persistence, OCI Object Storage for files and models).

## Operating Context

- **Delivery context:** Hackathon ONE (Alura + Oracle), team G9-LATAM-Team_40; two-week sprint; demo-oriented, not production deployment.
- **Runtime:** Docker Compose on VPS (or local dev): frontend Next.js, Spring Boot API `:8080`, FastAPI ML `:5000`, Supabase (PostgreSQL, GoTrue Auth, PostgREST), OCI Object Storage for models, datasets, and user files.
- **Core workflows:**
  1. Register / login (Supabase Auth JWT)
  2. Classify single document (title + text → category, probability, keywords, related content)
  3. Classify batch (multiple documents in one request)
  4. Upload files (PDF, TXT, MD, DOCX) to OCI with metadata in DB
  5. List and download user files
  6. Search classified content by keywords
  7. Dashboard: categories with counts, classified content cards, navigation between sections
- **Document categories (ML output):** Política SST, Procedimientos, Matrices de Riesgo, Registros, Auditorías, and related normative types as defined by the data-science model and API contract.
- **Frontend location:** `frontend/techisolutions/` (Next.js 16 App Router). Legacy Vite/React Router docs in `frontend/AGENTS.md` describe planned routes but the active scaffold is Next.js.

## Capabilities and Constraints

**Confirmed functionality (API contract):**

| Capability | Endpoint / surface |
|---|---|
| Auth register/login | `POST /auth/register`, `POST /auth/login` (delegated to Supabase GoTrue) |
| Classify text | `POST /api/contenido` |
| Classify batch | `POST /api/contenido/lote` |
| Search by keywords | `GET /api/contenido/buscar?q=` |
| List categories + counts | `GET /api/categorias` |
| Upload file | `POST /api/archivos` (multipart, max ~10MB) |
| List / get file URL | `GET /api/archivos`, `GET /api/archivos/{id}` |
| Health | `GET /actuator/health` |

**Technical constraints:**

- JWT required on protected API routes; frontend stores token and attaches `Authorization: Bearer`.
- Allowed upload types: PDF, TXT, MD, DOCX.
- ML service is internal (`POST /predict`); frontend never calls it directly.
- OCI Object Storage is mandatory Oracle Cloud integration; credentials may be stubbed during development.
- Data Science team owns `datascience/` independently; do not modify without coordination.
- Environment variables documented in root `.env.example`; never commit secrets.

**Terminology (preserve in UI copy):**

- SST = Seguridad y Salud en el Trabajo
- ISO 45001 primary; ISO 9001 / ISO 14001 as future standards
- Spanish-first product language (README, sprint plan, and team docs are Spanish)

**Undecided / open:**

- Production deployment target and public URL (hackathon demo only for now).
- Final production logo asset path (see Brand Commitments).

## Brand Commitments

- **Canonical product name:** TechISOlutions (not "TechContent AI" in user-facing copy; that name appears only in internal sprint/AGENTS docs).
- **Voice:** Professional, clear, compliance-oriented; Spanish primary for user-facing strings in this LATAM hackathon context.
- **Visual identity:** Logo or brand assets confirmed to exist and will be provided; not yet present in the repository at init time. Until the asset is added, UI may use a text wordmark "TechISOlutions" — do not invent a corporate identity beyond what the team supplies.
- **Oracle / Alura hackathon context** may appear in footer or about copy where appropriate; no false enterprise customer claims.

## Evidence on Hand

| Asset | Status |
|---|---|
| Logo / brand raster | To be provided by team; not in repo at init |
| Sample ISO documents (policies, matrices, etc.) | Available for demo content (user-confirmed; may live outside repo) |
| README API examples | `README.md` — realistic request/response JSON for classification and file upload |
| Sprint plan & API contract | `docs/sprint-plan.md` — DTO shapes, routes, error codes |
| Customers, testimonials, case studies | **None** — must not fabricate social proof |
| Production metrics, pricing, licensing | **None** — hackathon demo only |

Use README and sprint-plan examples for illustrative classified titles (e.g. "Política de Seguridad y Salud en el Trabajo", "Matriz de Riesgos Laborales") when demo data is needed in the UI.

## Product Principles

1. **Normative fidelity** — Categories, labels, and flows must reflect ISO 45001 document types and SST coordinator mental models, not generic "folders" or "tags."
2. **Traceability over novelty** — Keywords, related documents, and search support audit and retrieval; every classification should feel actionable in a compliance review.
3. **Honest automation** — Show model probability and let users see what the ML inferred; do not imply human review or certification where the product only classifies.
4. **End-to-end demo integrity** — Prioritize flows that work in the hackathon smoke test (auth → classify → upload → search → dashboard) over peripheral features.
5. **No fabricated proof** — No invented customers, testimonials, compliance guarantees, or production deployment claims.

## Accessibility & Inclusion

No product-specific accessibility standard mandated at init. Frontend stack commits to accessible components (shadcn/ui / Base UI). Prefer semantic HTML, keyboard-navigable forms, and sufficient contrast in all UI work; WCAG 2.1 AA is a reasonable default target for the web app unless the team sets a different requirement.
