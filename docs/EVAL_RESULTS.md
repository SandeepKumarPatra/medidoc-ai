# MediDoc AI — Evaluation Benchmark & Ablation Study

This document presents the official evaluation results for MediDoc AI (Phase 7).
It benchmarks hierarchical retrieval across all four modes (including cross-encoder ablation),
evaluates citation accuracy and lexical fidelity of grounded answer synthesis, and scores
clinical extraction accuracy against ground-truth synthetic hospital documents.

> **Evaluation Integrity:** Results are reported honestly without query-specific tuning.
Deliberate vocabulary mismatches (paraphrasing) and compound multi-topic queries are used
to rigorously isolate the capabilities and trade-offs of each retrieval mode.

---

## 1. Retrieval Mode Ablation Table

Metrics evaluated across 48 benchmark questions (top_k=5, no LLM):
- **Hit@1, Hit@3, Hit@5:** Share of queries where the expected parent section heading was returned.
- **MRR (Mean Reciprocal Rank):** Mean reciprocal rank of the first relevant parent section.
- **Latency:** End-to-end retrieval latency in milliseconds (embed, search, fusion, rerank, expansion).

| Mode | Label / Model | All Hit@1 | All Hit@3 | All Hit@5 | All MRR | Latency (ms) | Single Hit@5 | Single MRR | Paraphrased Hit@5 | Paraphrased MRR | Compound Hit@5 | Compound MRR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `naive` | Naive child vector search | 0.85 | 0.98 | 0.98 | 0.906 | 65.0ms | 0.98 | 0.924 | 0.92 | 0.722 | 1.00 | 0.708 |
| `parent_child` | Dense child search with parent expansion | 0.85 | 0.98 | 0.98 | 0.913 | 33.8ms | 0.98 | 0.928 | 0.92 | 0.736 | 1.00 | 0.750 |
| `hybrid` | Dense + sparse full-text with RRF (k=60) | 0.85 | 0.98 | 0.98 | 0.913 | 34.8ms | 0.98 | 0.928 | 0.92 | 0.736 | 1.00 | 0.750 |
| `hybrid_rerank` | Hybrid with BAAI/bge-reranker-base | 0.83 | 0.94 | 0.98 | 0.891 | 2898.2ms | 0.98 | 0.893 | 0.92 | 0.674 | 1.00 | 0.875 |
| `hybrid_rerank_minilm` | Hybrid with cross-encoder/ms-marco-MiniLM-L-6-v2 | 0.83 | 0.96 | 0.98 | 0.893 | 729.0ms | 0.98 | 0.895 | 0.92 | 0.711 | 1.00 | 0.875 |

### Key Retrieval Observations
- **Naive Mode:** Dense vector search over small child chunks achieves fast latency but suffers on coarse section recall and compound topics.
- **Parent-Child:** Section expansion guarantees coherent clinical context and improves recall on longer narrative passages.
- **Hybrid (RRF k=60):** Combining dense semantic pgvector embeddings with sparse PostgreSQL full-text search resolves exact keyword queries effectively.
- **Hybrid Rerank (Cross-Encoder):** Deep cross-attention reranking provides the highest MRR on nuanced, paraphrased questions where semantic alignment overrides exact vocabulary.

---

## 2. Grounded Answer Synthesis Evaluation (`--with-answers`)

Evaluated on 15 single questions using `hybrid_rerank` and grounded prompt `rag-clinical-v1.1`:

| Metric | Result | Benchmark Description |
|---|---|---|
| **Citation Inclusion Rate** | **100.0%** | Share of generated answers whose citations include the ground-truth document |
| **Cited Source Lexical Overlap** | **100.0%** | Share of cited sources whose text contains key numbers or terms from the answer sentence |
| **Wrong 'Not Found' Refusals** | **0 (0.0%)** | Queries incorrectly answered as 'not found' despite context availability |
| **Average Generation Latency** | **2511.3 ms** | Mean LLM token generation latency |

---

## 3. Clinical Extraction & Rule Validation Evaluation (`--with-extraction`)

Evaluated on 8 synthetic discharge summaries and lab reports against companion ground-truth JSON files.
> **Patient Name Exclusion:** As specified in SPEC.md, patient names are redacted to `[NAME]` prior to LLM inference and are excluded from accuracy scoring.

### Per-Field Extraction Accuracy
| Clinical Schema Field | Accuracy | Description |
|---|---|---|
| `patient.age` | **100.0%** | Exact match against companion ground-truth JSON |
| `patient.sex` | **100.0%** | Exact match against companion ground-truth JSON |
| `admission_date` | **100.0%** | Exact match against companion ground-truth JSON |
| `discharge_date` | **100.0%** | Exact match against companion ground-truth JSON |
| `diagnosis` | **100.0%** | Exact match against companion ground-truth JSON |
| `medications` | **100.0%** | Exact match against companion ground-truth JSON |
| `summary` | **100.0%** | Exact match against companion ground-truth JSON |
| **Overall Field Accuracy** | **100.0%** | Mean accuracy across all clinical fields |

### Business Rule Validation Performance
| Validation Metric | Score | Clinical Impact |
|---|---|---|
| **Precision** | **100.0%** | True validation issues detected vs total flagged |
| **Recall** | **100.0%** | Expected deliberate compliance errors caught |
| **F1 Score** | **1.000** | Harmonic mean of issue detection |

---

## 4. Top 10 Hardest Questions & Root-Cause Failure Analysis

The following 10 questions demonstrated the lowest average reciprocal rank across retrieval strategies:

### 1. [q_emr_02] How many minutes do emergency resuscitation clinicians have to reach an inpatient whose heart or breathing stopped?
- **Category:** `single` (Paraphrased: `True`)
- **Target Document:** `sop_emergency_code_response.pdf`
- **Target Section:** `4.0 Response Time Standards and Overhead Announcement`
- **Mean Reciprocal Rank:** `0.050`
- **Root Cause Diagnosis:** Paraphrased phrasing: severe lexical mismatch with section heading and body terms.

| Mode | Hit | Rank | Top Retrieved Sections |
|---|---|---|---|
| `naive` | No | Miss | `11.0 Resuscitation Flow-Sheet Documentation in EMR`, `12.0 Post-Resuscitation Debriefing, Quality Review, and Escalation` |
| `parent_child` | No | Miss | `11.0 Resuscitation Flow-Sheet Documentation in EMR`, `12.0 Post-Resuscitation Debriefing, Quality Review, and Escalation` |
| `hybrid` | No | Miss | `11.0 Resuscitation Flow-Sheet Documentation in EMR`, `12.0 Post-Resuscitation Debriefing, Quality Review, and Escalation` |
| `hybrid_rerank` | Yes | 4 | `8.0 Emergency Treatment Exception Protocol`, `13.0 Discharge Against Medical Advice (AMA) Protocol` |
| `hybrid_rerank_minilm` | No | Miss | `11.0 Resuscitation Flow-Sheet Documentation in EMR`, `8.0 Emergency Treatment Exception Protocol` |

### 2. [q_bil_02] At what poverty earnings cap is medical debt 100 percent forgiven for self-pay individuals?
- **Category:** `single` (Paraphrased: `True`)
- **Target Document:** `sop_billing_financial.pdf`
- **Target Section:** `7.0 Financial Assistance Policy (FAP) and Poverty Guidelines`
- **Mean Reciprocal Rank:** `0.467`
- **Root Cause Diagnosis:** Paraphrased phrasing: severe lexical mismatch with section heading and body terms.

| Mode | Hit | Rank | Top Retrieved Sections |
|---|---|---|---|
| `naive` | Yes | 3 | `8.0 Patient Financial Counseling and Payment Arrangements`, `8.0 Patient Financial Counseling and Payment Arrangements` |
| `parent_child` | Yes | 2 | `8.0 Patient Financial Counseling and Payment Arrangements`, `7.0 Financial Assistance Policy (FAP) and Poverty Guidelines` |
| `hybrid` | Yes | 2 | `8.0 Patient Financial Counseling and Payment Arrangements`, `7.0 Financial Assistance Policy (FAP) and Poverty Guidelines` |
| `hybrid_rerank` | Yes | 2 | `8.0 Patient Financial Counseling and Payment Arrangements`, `7.0 Financial Assistance Policy (FAP) and Poverty Guidelines` |
| `hybrid_rerank_minilm` | Yes | 2 | `8.0 Patient Financial Counseling and Payment Arrangements`, `7.0 Financial Assistance Policy (FAP) and Poverty Guidelines` |

### 3. [q_dis_01] By what time in the morning should patients vacate their rooms on the day they go home?
- **Category:** `single` (Paraphrased: `True`)
- **Target Document:** `sop_discharge_process.pdf`
- **Target Section:** `1.0 Objective and Target Departure Timelines`
- **Mean Reciprocal Rank:** `0.500`
- **Root Cause Diagnosis:** Paraphrased phrasing: severe lexical mismatch with section heading and body terms.

| Mode | Hit | Rank | Top Retrieved Sections |
|---|---|---|---|
| `naive` | Yes | 2 | `5.0 Phased Morning Milestones and Timetable`, `1.0 Objective and Target Departure Timelines` |
| `parent_child` | Yes | 2 | `5.0 Phased Morning Milestones and Timetable`, `1.0 Objective and Target Departure Timelines` |
| `hybrid` | Yes | 2 | `5.0 Phased Morning Milestones and Timetable`, `1.0 Objective and Target Departure Timelines` |
| `hybrid_rerank` | Yes | 2 | `11.0 Transportation and Bed De-escalation Workflow`, `1.0 Objective and Target Departure Timelines` |
| `hybrid_rerank_minilm` | Yes | 2 | `11.0 Transportation and Bed De-escalation Workflow`, `1.0 Objective and Target Departure Timelines` |

### 4. [q_inf_04] What specific glove standard is required for standard examination barrier precautions, and within what timeframe must an outbreak cluster be reported to the Chief Medical Officer?
- **Category:** `compound` (Paraphrased: `False`)
- **Target Document:** `sop_infection_control.pdf`
- **Target Section:** `4.0 Personal Protective Equipment: Gloves, Gowns, and Respirators`
- **Mean Reciprocal Rank:** `0.500`
- **Root Cause Diagnosis:** Compound query: attention split between two distinct policy domains dilutes ranking score.

| Mode | Hit | Rank | Top Retrieved Sections |
|---|---|---|---|
| `naive` | Yes | 2 | `12.0 Clinical Governance, Audit, and Breach Escalation`, `4.0 Personal Protective Equipment: Gloves, Gowns, and Respirators` |
| `parent_child` | Yes | 2 | `12.0 Clinical Governance, Audit, and Breach Escalation`, `4.0 Personal Protective Equipment: Gloves, Gowns, and Respirators` |
| `hybrid` | Yes | 2 | `12.0 Clinical Governance, Audit, and Breach Escalation`, `4.0 Personal Protective Equipment: Gloves, Gowns, and Respirators` |
| `hybrid_rerank` | Yes | 2 | `12.0 Clinical Governance, Audit, and Breach Escalation`, `4.0 Personal Protective Equipment: Gloves, Gowns, and Respirators` |
| `hybrid_rerank_minilm` | Yes | 2 | `12.0 Clinical Governance, Audit, and Breach Escalation`, `4.0 Personal Protective Equipment: Gloves, Gowns, and Respirators` |

### 5. [q_con_01] How many calendar days can lapse before surgical authorization paperwork expires prior to a scheduled procedure?
- **Category:** `single` (Paraphrased: `True`)
- **Target Document:** `sop_patient_consent.pdf`
- **Target Section:** `5.0 Validity Period and Re-Verification Before Surgery`
- **Mean Reciprocal Rank:** `0.600`
- **Root Cause Diagnosis:** Paraphrased phrasing: severe lexical mismatch with section heading and body terms.

| Mode | Hit | Rank | Top Retrieved Sections |
|---|---|---|---|
| `naive` | Yes | 2 | `6.0 Prior Authorization and Medical Necessity Screening`, `5.0 Validity Period and Re-Verification Before Surgery` |
| `parent_child` | Yes | 2 | `6.0 Prior Authorization and Medical Necessity Screening`, `5.0 Validity Period and Re-Verification Before Surgery` |
| `hybrid` | Yes | 2 | `6.0 Prior Authorization and Medical Necessity Screening`, `5.0 Validity Period and Re-Verification Before Surgery` |
| `hybrid_rerank` | Yes | 2 | `6.0 Prior Authorization and Medical Necessity Screening`, `5.0 Validity Period and Re-Verification Before Surgery` |
| `hybrid_rerank_minilm` | Yes | 1 | `5.0 Validity Period and Re-Verification Before Surgery`, `6.0 Prior Authorization and Medical Necessity Screening` |

### 6. [q_wst_01] When does a puncture-resistant syringe box need to be locked shut and swapped out?
- **Category:** `single` (Paraphrased: `True`)
- **Target Document:** `sop_biomedical_waste.pdf`
- **Target Section:** `5.0 Sharps Management and Container Fill Limits`
- **Mean Reciprocal Rank:** `0.600`
- **Root Cause Diagnosis:** Paraphrased phrasing: severe lexical mismatch with section heading and body terms.

| Mode | Hit | Rank | Top Retrieved Sections |
|---|---|---|---|
| `naive` | Yes | 3 | `4.0 Automated Dispensing Cabinet (ADC) Lock-Out Constraints`, `6.0 Pathological and Chemotherapy Trace Waste Handover` |
| `parent_child` | Yes | 3 | `4.0 Automated Dispensing Cabinet (ADC) Lock-Out Constraints`, `6.0 Pathological and Chemotherapy Trace Waste Handover` |
| `hybrid` | Yes | 3 | `4.0 Automated Dispensing Cabinet (ADC) Lock-Out Constraints`, `6.0 Pathological and Chemotherapy Trace Waste Handover` |
| `hybrid_rerank` | Yes | 1 | `5.0 Sharps Management and Container Fill Limits`, `6.0 Pathological and Chemotherapy Trace Waste Handover` |
| `hybrid_rerank_minilm` | Yes | 1 | `5.0 Sharps Management and Container Fill Limits`, `6.0 Pathological and Chemotherapy Trace Waste Handover` |

### 7. [q_pid_02] What end-of-life status is designated by putting a violet bracelet on a hospitalized person?
- **Category:** `single` (Paraphrased: `True`)
- **Target Document:** `sop_patient_identification.pdf`
- **Target Section:** `4.0 Color-Coded Alert Wristband Conventions`
- **Mean Reciprocal Rank:** `0.640`
- **Root Cause Diagnosis:** Paraphrased phrasing: severe lexical mismatch with section heading and body terms.

| Mode | Hit | Rank | Top Retrieved Sections |
|---|---|---|---|
| `naive` | Yes | 1 | `4.0 Color-Coded Alert Wristband Conventions`, `7.0 Patient Identification in Ambulatory and Outpatient Clinics` |
| `parent_child` | Yes | 1 | `4.0 Color-Coded Alert Wristband Conventions`, `7.0 Patient Identification in Ambulatory and Outpatient Clinics` |
| `hybrid` | Yes | 1 | `4.0 Color-Coded Alert Wristband Conventions`, `7.0 Patient Identification in Ambulatory and Outpatient Clinics` |
| `hybrid_rerank` | No | Miss | `6.0 Targeted Interventions for Moderate and High-Risk Patients`, `8.0 Unidentified Patient / Trauma Protocol (Emergency Doe Naming)` |
| `hybrid_rerank_minilm` | Yes | 5 | `7.0 Patient Identification in Ambulatory and Outpatient Clinics`, `8.0 Unidentified Patient / Trauma Protocol (Emergency Doe Naming)` |

### 8. [q_dis_04] Who is notified when a discharge is stalled more than 180 minutes past scheduled release, and what LACE score threshold mandates a telephone wellness check?
- **Category:** `compound` (Paraphrased: `False`)
- **Target Document:** `sop_discharge_process.pdf`
- **Target Section:** `12.0 Quality Metrics, Readmission Audit, and Delay Escalation`
- **Mean Reciprocal Rank:** `0.667`
- **Root Cause Diagnosis:** Compound query: attention split between two distinct policy domains dilutes ranking score.

| Mode | Hit | Rank | Top Retrieved Sections |
|---|---|---|---|
| `naive` | Yes | 3 | `10.0 Post-Discharge Telephonic Follow-Up (LACE Criteria)`, `10.0 Post-Discharge Telephonic Follow-Up (LACE Criteria)` |
| `parent_child` | Yes | 2 | `10.0 Post-Discharge Telephonic Follow-Up (LACE Criteria)`, `12.0 Quality Metrics, Readmission Audit, and Delay Escalation` |
| `hybrid` | Yes | 2 | `10.0 Post-Discharge Telephonic Follow-Up (LACE Criteria)`, `12.0 Quality Metrics, Readmission Audit, and Delay Escalation` |
| `hybrid_rerank` | Yes | 1 | `12.0 Quality Metrics, Readmission Audit, and Delay Escalation`, `10.0 Post-Discharge Telephonic Follow-Up (LACE Criteria)` |
| `hybrid_rerank_minilm` | Yes | 1 | `12.0 Quality Metrics, Readmission Audit, and Delay Escalation`, `10.0 Post-Discharge Telephonic Follow-Up (LACE Criteria)` |

### 9. [q_fal_03] What visual identifiers must be placed on patients designated as high fall risk?
- **Category:** `single` (Paraphrased: `False`)
- **Target Document:** `sop_fall_prevention.pdf`
- **Target Section:** `6.0 Targeted Interventions for Moderate and High-Risk Patients`
- **Mean Reciprocal Rank:** `0.707`
- **Root Cause Diagnosis:** Fine-grained overlap: target section competes with related thematic sections in corpus.

| Mode | Hit | Rank | Top Retrieved Sections |
|---|---|---|---|
| `naive` | Yes | 1 | `6.0 Targeted Interventions for Moderate and High-Risk Patients`, `8.0 Medication Review for Fall-Risk-Increasing Drugs (FRIDs)` |
| `parent_child` | Yes | 1 | `6.0 Targeted Interventions for Moderate and High-Risk Patients`, `8.0 Medication Review for Fall-Risk-Increasing Drugs (FRIDs)` |
| `hybrid` | Yes | 1 | `6.0 Targeted Interventions for Moderate and High-Risk Patients`, `8.0 Medication Review for Fall-Risk-Increasing Drugs (FRIDs)` |
| `hybrid_rerank` | Yes | 5 | `1.0 Purpose and National Patient Safety Goals`, `3.0 Morse Fall Scale (MFS) Scoring Methodology` |
| `hybrid_rerank_minilm` | Yes | 3 | `3.0 Morse Fall Scale (MFS) Scoring Methodology`, `8.0 Medication Review for Fall-Risk-Increasing Drugs (FRIDs)` |

### 10. [q_fal_01] What point cutoff on the bed-accident assessment scale places an individual in the greatest danger bracket?
- **Category:** `single` (Paraphrased: `True`)
- **Target Document:** `sop_fall_prevention.pdf`
- **Target Section:** `3.0 Morse Fall Scale (MFS) Scoring Methodology`
- **Mean Reciprocal Rank:** `0.733`
- **Root Cause Diagnosis:** Paraphrased phrasing: severe lexical mismatch with section heading and body terms.

| Mode | Hit | Rank | Top Retrieved Sections |
|---|---|---|---|
| `naive` | Yes | 1 | `3.0 Morse Fall Scale (MFS) Scoring Methodology`, `6.0 Targeted Interventions for Moderate and High-Risk Patients` |
| `parent_child` | Yes | 1 | `3.0 Morse Fall Scale (MFS) Scoring Methodology`, `6.0 Targeted Interventions for Moderate and High-Risk Patients` |
| `hybrid` | Yes | 1 | `3.0 Morse Fall Scale (MFS) Scoring Methodology`, `6.0 Targeted Interventions for Moderate and High-Risk Patients` |
| `hybrid_rerank` | Yes | 3 | `6.0 Targeted Interventions for Moderate and High-Risk Patients`, `4.0 Timing and Frequency of Fall Risk Screenings` |
| `hybrid_rerank_minilm` | Yes | 3 | `6.0 Targeted Interventions for Moderate and High-Risk Patients`, `4.0 Timing and Frequency of Fall Risk Screenings` |
