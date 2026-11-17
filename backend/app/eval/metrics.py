"""Evaluation metrics calculation for retrieval ablation, QA answers, and clinical extraction.

Calculates:
1. Retrieval Metrics: hit@1, hit@3, hit@5, MRR, latency, segmented by query category
   (overall, single, paraphrased, compound).
2. QA Answer Metrics: citation inclusion of expected document, cited source lexical
   overlap with answer, wrong 'not found' refusal rate, generation latency.
3. Extraction Metrics: per-field clinical schema accuracy (excluding patient name)
   and precision/recall/F1 of detected business rule validation issues.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.eval.schemas import (
    AnswerEvalDetail,
    AnswersEvalSummary,
    CategoryBreakdown,
    ExtractionEvalSummary,
    ExtractionReportDetail,
    HybridVsDenseComparison,
    MetricScores,
    QuestionEvalItem,
    UnanswerableDetail,
    UnanswerableEvalSummary,
)

STOPWORDS: Set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "were", "will", "with", "what", "when", "where", "which",
    "who", "how", "must", "should", "than", "this", "they", "their", "hospital",
    "patient", "policy", "standard", "procedure",
}


def compute_retrieval_metrics(
    eval_items: List[QuestionEvalItem],
) -> MetricScores:
    """Compute hit@1, hit@3, hit@5, MRR, latency, and compound both-hit@5."""
    total = len(eval_items)
    if total == 0:
        return MetricScores()

    hit_1_count = 0
    hit_3_count = 0
    hit_5_count = 0
    mrr_sum = 0.0
    latency_sum = 0.0

    for item in eval_items:
        latency_sum += item.latency_ms
        mrr_sum += item.reciprocal_rank

        if item.rank is not None:
            if item.rank == 1:
                hit_1_count += 1
            if item.rank <= 3:
                hit_3_count += 1
            if item.rank <= 5:
                hit_5_count += 1

    both_hit_items = [item for item in eval_items if item.both_hit_at_5 is not None]
    compound_both_hit = None
    if both_hit_items:
        compound_both_hit = round(
            sum(1 for item in both_hit_items if item.both_hit_at_5) / len(both_hit_items),
            4,
        )

    return MetricScores(
        total_questions=total,
        hit_at_1=round(hit_1_count / total, 4),
        hit_at_3=round(hit_3_count / total, 4),
        hit_at_5=round(hit_5_count / total, 4),
        mrr=round(mrr_sum / total, 4),
        avg_latency_ms=round(latency_sum / total, 2),
        compound_both_hit_at_5=compound_both_hit,
    )


def compute_category_breakdown(
    eval_items: List[QuestionEvalItem],
) -> CategoryBreakdown:
    """Compute retrieval performance segmented across query archetypes."""
    all_metrics = compute_retrieval_metrics(eval_items)

    single_items = [i for i in eval_items if i.category == "single"]
    single_metrics = compute_retrieval_metrics(single_items)

    paraphrased_items = [i for i in eval_items if i.paraphrased]
    paraphrased_metrics = compute_retrieval_metrics(paraphrased_items)

    keyword_items = [i for i in eval_items if i.category == "keyword"]
    keyword_metrics = compute_retrieval_metrics(keyword_items)

    compound_items = [i for i in eval_items if i.category == "compound"]
    compound_metrics = compute_retrieval_metrics(compound_items)

    return CategoryBreakdown(
        all=all_metrics,
        single=single_metrics,
        paraphrased=paraphrased_metrics,
        keyword=keyword_metrics,
        compound=compound_metrics,
    )


def is_not_found_response(raw_answer: str) -> bool:
    """Determine whether an answer indicates a refusal or 'not found' outcome."""
    not_found_phrases = [
        "not found in the provided hospital documentation",
        "was not found in the provided",
        "the answer was not found",
        "not mentioned in the provided",
        "cannot answer this question based on the provided",
        "does not contain sufficient information",
        "not contained in the provided",
        "not found in the provided",
        "not found in provided",
        "unable to find",
        "cannot be found",
        "no information is provided",
        "no information provided",
    ]
    raw_lower = raw_answer.lower()
    return any(p in raw_lower for p in not_found_phrases)


def evaluate_single_answer(
    question_data: Dict[str, Any],
    answer_result: Any,  # AnswerResult from qa.py
) -> AnswerEvalDetail:
    """Evaluate a single grounded /ask pipeline response against ground truth."""
    qid = question_data.get("id", "")
    q_text = question_data.get("question", "")
    expected_doc = question_data.get("expected_doc", "")
    expected_sec = question_data.get("expected_section", "")

    raw_answer = answer_result.answer
    timings = getattr(answer_result, "timings", {})
    gen_ms = float(timings.get("generation_ms", 0.0))

    # (a) Check citations include expected document
    cited_sources = getattr(answer_result, "citations", [])
    cited_docs = {getattr(c, "document", "") for c in cited_sources}
    citations_include_expected = expected_doc in cited_docs

    # (b) Check lexical/numerical overlap between answer sentences and cited source text
    overlap_details: List[Dict[str, Any]] = []
    sources = getattr(answer_result, "sources", [])
    source_map: Dict[int, str] = {}
    for idx, s in enumerate(sources, start=1):
        source_map[idx] = getattr(s, "citation", "")

    num_pattern = re.compile(r"\b\d+(?:\.\d+)?%?\b")
    word_pattern = re.compile(r"\b[A-Za-z]{4,}\b")

    answer_numbers = set(num_pattern.findall(raw_answer))
    answer_words = {
        w.lower()
        for w in word_pattern.findall(raw_answer)
        if w.lower() not in STOPWORDS
    }

    for cited in cited_sources:
        s_idx = getattr(cited, "source_index", None)
        src_text = ""
        if s_idx and 1 <= s_idx <= len(sources):
            src_obj = sources[s_idx - 1]
            src_text = getattr(src_obj, "citation", "") + " " + getattr(src_obj, "section_title", "")
        for s in sources:
            if getattr(s, "document", "") == getattr(cited, "document", ""):
                src_text += " " + (getattr(s, "section_title", "") or "")

        src_lower = src_text.lower()
        matched_numbers = [n for n in answer_numbers if n.lower() in src_lower]
        matched_terms = [w for w in answer_words if w in src_lower]

        has_overlap = bool(matched_numbers or matched_terms)
        overlap_details.append(
            {
                "source_index": s_idx,
                "document": getattr(cited, "document", ""),
                "section": getattr(cited, "section_title", ""),
                "has_overlap": has_overlap,
                "matched_numbers": matched_numbers[:3],
                "matched_terms": matched_terms[:3],
            }
        )

    # (c) Wrong 'not found' refusal detection
    is_refusal = is_not_found_response(raw_answer)
    is_wrong_not_found = is_refusal

    return AnswerEvalDetail(
        question_id=qid,
        question=q_text,
        expected_doc=expected_doc,
        expected_section=expected_sec,
        answer=raw_answer,
        citations_include_expected_doc=citations_include_expected,
        cited_sources_overlap=overlap_details,
        is_wrong_not_found=is_wrong_not_found,
        generation_ms=gen_ms,
    )


def summarize_answers_evaluation(
    eval_details: List[AnswerEvalDetail],
) -> AnswersEvalSummary:
    """Summarize answer evaluation metrics across the evaluated questions."""
    total = len(eval_details)
    if total == 0:
        return AnswersEvalSummary()

    doc_inclusion_count = sum(1 for d in eval_details if d.citations_include_expected_doc)
    wrong_not_found_count = sum(1 for d in eval_details if d.is_wrong_not_found)
    total_gen_ms = sum(d.generation_ms for d in eval_details)

    # Calculate share of cited sources with key term or number overlap
    total_cited_sources = 0
    overlapping_cited_sources = 0
    for d in eval_details:
        for overlap in d.cited_sources_overlap:
            total_cited_sources += 1
            if overlap.get("has_overlap"):
                overlapping_cited_sources += 1

    overlap_rate = (
        round(overlapping_cited_sources / total_cited_sources, 4)
        if total_cited_sources > 0
        else 0.0
    )

    return AnswersEvalSummary(
        total_evaluated=total,
        citation_inclusion_rate=round(doc_inclusion_count / total, 4),
        key_term_overlap_rate=overlap_rate,
        wrong_not_found_count=wrong_not_found_count,
        wrong_not_found_rate=round(wrong_not_found_count / total, 4),
        avg_generation_ms=round(total_gen_ms / total, 2),
        details=eval_details,
    )


def evaluate_unanswerable_question(
    question_data: Dict[str, Any],
    answer_result: Any,
) -> UnanswerableDetail:
    """Evaluate whether an unanswerable question correctly returned a 'not found' response."""
    qid = question_data.get("id", "")
    q_text = question_data.get("question", "")
    raw_answer = getattr(answer_result, "answer", str(answer_result))
    timings = getattr(answer_result, "timings", {})
    gen_ms = float(timings.get("generation_ms", 0.0))

    is_refusal = is_not_found_response(raw_answer)

    return UnanswerableDetail(
        question_id=qid,
        question=q_text,
        answer=raw_answer,
        correctly_not_found=is_refusal,
        wrongly_produced_answer=not is_refusal,
        generation_ms=gen_ms,
    )


def summarize_unanswerable_evaluation(
    details: List[UnanswerableDetail],
) -> UnanswerableEvalSummary:
    """Summarize metrics across unanswerable questions benchmark."""
    total = len(details)
    if total == 0:
        return UnanswerableEvalSummary()

    correct_count = sum(1 for d in details if d.correctly_not_found)
    wrong_count = sum(1 for d in details if d.wrongly_produced_answer)
    total_gen_ms = sum(d.generation_ms for d in details)

    return UnanswerableEvalSummary(
        total_evaluated=total,
        correctly_not_found_count=correct_count,
        correctly_not_found_rate=round(correct_count / total, 4),
        wrongly_produced_count=wrong_count,
        wrongly_produced_rate=round(wrong_count / total, 4),
        avg_generation_ms=round(total_gen_ms / total, 2),
        details=details,
    )


def compare_hybrid_vs_dense(
    parent_child_items: List[QuestionEvalItem],
    hybrid_items: List[QuestionEvalItem],
) -> HybridVsDenseComparison:
    """Compare top-1 and top-5 retrieved sections between hybrid and dense (parent_child) search."""
    total = len(parent_child_items)
    if total == 0 or len(hybrid_items) != total:
        return HybridVsDenseComparison()

    hybrid_map = {item.question_id: item for item in hybrid_items}
    diff_top1 = 0
    diff_top5 = 0

    for pc_item in parent_child_items:
        h_item = hybrid_map.get(pc_item.question_id)
        if not h_item:
            continue

        if pc_item.retrieved_docs and h_item.retrieved_docs:
            pc_top1 = (
                pc_item.retrieved_docs[0] if pc_item.retrieved_docs else "",
                pc_item.retrieved_section_titles[0] if pc_item.retrieved_section_titles else "",
            )
            h_top1 = (
                h_item.retrieved_docs[0] if h_item.retrieved_docs else "",
                h_item.retrieved_section_titles[0] if h_item.retrieved_section_titles else "",
            )
            pc_top5 = list(zip(pc_item.retrieved_docs[:5], pc_item.retrieved_section_titles[:5]))
            h_top5 = list(zip(h_item.retrieved_docs[:5], h_item.retrieved_section_titles[:5]))
        else:
            pc_top1 = pc_item.retrieved_section_titles[0] if pc_item.retrieved_section_titles else ""
            h_top1 = h_item.retrieved_section_titles[0] if h_item.retrieved_section_titles else ""
            pc_top5 = pc_item.retrieved_section_titles[:5]
            h_top5 = h_item.retrieved_section_titles[:5]

        if pc_top1 != h_top1:
            diff_top1 += 1

        if pc_top5 != h_top5:
            diff_top5 += 1

    return HybridVsDenseComparison(
        total_questions=total,
        different_top_1_count=diff_top1,
        different_top_1_rate=round(diff_top1 / total, 4),
        different_top_5_count=diff_top5,
        different_top_5_rate=round(diff_top5 / total, 4),
    )


def evaluate_clinical_extraction(
    extracted_dict: Dict[str, Any],
    ground_truth_dict: Dict[str, Any],
    detected_issues: List[Any],
) -> ExtractionReportDetail:
    """Evaluate extracted structured clinical data and validation issues against ground truth."""
    field_matches: Dict[str, bool] = {}

    # 1. Patient Age (exact int match)
    ext_age = extracted_dict.get("patient", {}).get("age")
    gt_age = ground_truth_dict.get("patient", {}).get("age")
    field_matches["patient.age"] = (ext_age == gt_age)

    # 2. Patient Sex (exact string match)
    ext_sex = str(extracted_dict.get("patient", {}).get("sex", "")).strip().upper()
    gt_sex = str(ground_truth_dict.get("patient", {}).get("sex", "")).strip().upper()
    field_matches["patient.sex"] = (ext_sex == gt_sex)

    # 3. Admission Date (YYYY-MM-DD match)
    ext_adm = str(extracted_dict.get("admission_date", "")).strip()
    gt_adm = str(ground_truth_dict.get("admission_date", "")).strip()
    field_matches["admission_date"] = (ext_adm == gt_adm)

    # 4. Discharge Date (YYYY-MM-DD match)
    ext_dis = str(extracted_dict.get("discharge_date", "")).strip()
    gt_dis = str(ground_truth_dict.get("discharge_date", "")).strip()
    field_matches["discharge_date"] = (ext_dis == gt_dis)

    # 5. Diagnosis (set overlap - all ground truth diagnoses recognized)
    ext_diag = [str(d).lower().strip() for d in extracted_dict.get("diagnosis", []) if d]
    gt_diag = [str(d).lower().strip() for d in ground_truth_dict.get("diagnosis", []) if d]
    if not gt_diag:
        field_matches["diagnosis"] = (len(ext_diag) == 0)
    else:
        # Check if every ground truth diagnosis has a substring or close match in extracted
        matched_diag = 0
        for gd in gt_diag:
            if any(gd in ed or ed in gd for ed in ext_diag):
                matched_diag += 1
        field_matches["diagnosis"] = (matched_diag == len(gt_diag))

    # 6. Medications (names and dosages match)
    ext_meds = extracted_dict.get("medications", [])
    gt_meds = ground_truth_dict.get("medications", [])
    if not gt_meds:
        field_matches["medications"] = (len(ext_meds) == 0)
    else:
        matched_meds = 0
        for gm in gt_meds:
            gm_name = str(gm.get("name", "")).lower()
            gm_dose = gm.get("dose")
            gm_unit = str(gm.get("unit") or "").lower()
            for em in ext_meds:
                em_name = str(em.get("name", "")).lower()
                em_dose = em.get("dose")
                em_unit = str(em.get("unit") or "").lower()
                if gm_name in em_name or em_name in gm_name:
                    if em_dose == gm_dose and em_unit == gm_unit:
                        matched_meds += 1
                        break
        field_matches["medications"] = (matched_meds == len(gt_meds))

    # 7. Summary (non-empty clinical narrative)
    ext_summary = str(extracted_dict.get("summary", "")).strip()
    field_matches["summary"] = (len(ext_summary) >= 15)

    # 8. Validation Issues Precision and Recall
    meta = ground_truth_dict.get("_metadata", {})
    expected_issues = meta.get("expected_validation_issues", [])

    expected_rules = set()
    for iss in expected_issues:
        r = iss.get("rule") if isinstance(iss, dict) else getattr(iss, "rule", None)
        if r:
            expected_rules.add(r)

    detected_rules = set()
    for iss in detected_issues:
        r = iss.get("rule") if isinstance(iss, dict) else getattr(iss, "rule", None)
        if r:
            detected_rules.add(r)

    tp = len(detected_rules & expected_rules)
    fp = len(detected_rules - expected_rules)
    fn = len(expected_rules - detected_rules)

    validation_matches = {
        "expected_count": len(expected_rules),
        "detected_count": len(detected_rules),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "expected_rules": list(expected_rules),
        "detected_rules": list(detected_rules),
    }

    return ExtractionReportDetail(
        report_filename=ground_truth_dict.get("_metadata", {}).get("report_title", "report.pdf"),
        field_matches=field_matches,
        validation_matches=validation_matches,
    )


def summarize_extraction_evaluation(
    report_details: List[ExtractionReportDetail],
) -> ExtractionEvalSummary:
    """Summarize extraction accuracy and validation issue precision/recall across reports."""
    total = len(report_details)
    if total == 0:
        return ExtractionEvalSummary()

    field_sums: Dict[str, int] = {}
    field_counts: Dict[str, int] = {}
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for rep in report_details:
        for field, matched in rep.field_matches.items():
            field_sums[field] = field_sums.get(field, 0) + (1 if matched else 0)
            field_counts[field] = field_counts.get(field, 0) + 1

        v_match = rep.validation_matches
        total_tp += v_match.get("tp", 0)
        total_fp += v_match.get("fp", 0)
        total_fn += v_match.get("fn", 0)

    field_accuracy = {
        f: round(field_sums[f] / field_counts[f], 4)
        for f in field_sums
    }
    overall_acc = round(
        sum(field_accuracy.values()) / len(field_accuracy), 4
    ) if field_accuracy else 0.0

    precision = (
        round(total_tp / (total_tp + total_fp), 4)
        if (total_tp + total_fp) > 0
        else 1.0
    )
    recall = (
        round(total_tp / (total_tp + total_fn), 4)
        if (total_tp + total_fn) > 0
        else 1.0
    )
    f1 = (
        round(2 * precision * recall / (precision + recall), 4)
        if (precision + recall) > 0
        else 0.0
    )

    return ExtractionEvalSummary(
        total_reports=total,
        field_accuracy=field_accuracy,
        overall_field_accuracy=overall_acc,
        validation_precision=precision,
        validation_recall=recall,
        validation_f1=f1,
        details=report_details,
    )
