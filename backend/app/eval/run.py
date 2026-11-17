"""CLI entrypoint for running the MediDoc AI Phase 7 evaluation harness.

Usage:
    python -m backend.app.eval.run --modes all --with-answers --with-extraction
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
from typing import Dict, List, Optional

from backend.app.db.session import SessionLocal
from backend.app.eval.runner import (
    RERANKER_BGE,
    RERANKER_MINILM,
    generate_evaluation_markdown,
    identify_worst_questions,
    load_sop_questions,
    run_answers_evaluation,
    run_extraction_evaluation,
    run_retrieval_mode_evaluation,
)
from backend.app.eval.schemas import (
    AnswersEvalSummary,
    ExtractionEvalSummary,
    ModeEvalSummary,
    QuestionEvalItem,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("eval_cli")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="MediDoc AI Evaluation Harness & Ablation Runner (Phase 7)"
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["all"],
        help="Retrieval modes to run: 'all', 'naive', 'parent_child', 'hybrid', 'hybrid_rerank', 'hybrid_rerank_minilm'",
    )
    parser.add_argument(
        "--with-answers",
        action="store_true",
        default=False,
        help="Evaluate full grounded /ask pipeline on 15 single questions",
    )
    parser.add_argument(
        "--with-extraction",
        action="store_true",
        default=False,
        help="Evaluate clinical extraction and validation rules on 8 synthetic reports",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/EVAL_RESULTS.md",
        help="Output markdown file path (default: docs/EVAL_RESULTS.md)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top-K retrieval depth (default: 5)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=15,
        help="Number of single questions for --with-answers (default: 15)",
    )
    return parser.parse_args()


def main() -> None:
    """Main CLI execution flow."""
    args = parse_args()
    db = SessionLocal()

    try:
        questions = load_sop_questions()
        logger.info("Loaded %d benchmark questions from sop_questions.json", len(questions))

        # Determine modes to evaluate
        requested_modes: List[str] = []
        for m in args.modes:
            if "," in m:
                requested_modes.extend([sub.strip() for sub in m.split(",") if sub.strip()])
            else:
                requested_modes.append(m.strip())

        if "all" in requested_modes:
            modes_to_run = [
                ("naive", None, "Naive child vector search"),
                ("parent_child", None, "Dense child search with parent expansion"),
                ("hybrid", None, "Dense + sparse full-text with RRF (k=60)"),
                ("hybrid_rerank", RERANKER_BGE, "Hybrid with BAAI/bge-reranker-base"),
                ("hybrid_rerank", RERANKER_MINILM, "Hybrid with cross-encoder/ms-marco-MiniLM-L-6-v2"),
            ]
        else:
            modes_to_run = []
            for m in requested_modes:
                if m == "naive":
                    modes_to_run.append(("naive", None, "Naive child vector search"))
                elif m == "parent_child":
                    modes_to_run.append(("parent_child", None, "Dense child search with parent expansion"))
                elif m == "hybrid":
                    modes_to_run.append(("hybrid", None, "Dense + sparse full-text with RRF (k=60)"))
                elif m in ("hybrid_rerank", "hybrid_rerank_bge"):
                    modes_to_run.append(("hybrid_rerank", RERANKER_BGE, "Hybrid with BAAI/bge-reranker-base"))
                elif m in ("hybrid_rerank_minilm", "hybrid_rerank_msmarco"):
                    modes_to_run.append(("hybrid_rerank", RERANKER_MINILM, "Hybrid with cross-encoder/ms-marco-MiniLM-L-6-v2"))
                else:
                    logger.warning("Unrecognized mode '%s', skipping.", m)

        mode_summaries: List[ModeEvalSummary] = []
        all_mode_items: Dict[str, List[QuestionEvalItem]] = {}

        # 1. Run Retrieval Mode Evaluations
        print("\n" + "=" * 80)
        print("STARTING RETRIEVAL BENCHMARK EVALUATION (top_k=5)")
        print("=" * 80)

        for mode_key, reranker_model, label_note in modes_to_run:
            display_name = (
                f"{mode_key} ({reranker_model.split('/')[-1]})"
                if reranker_model
                else mode_key
            )
            print(f"\n--> Running mode: {display_name} ...")
            summary, items = run_retrieval_mode_evaluation(
                db=db,
                questions=questions,
                mode=mode_key,
                top_k=args.top_k,
                reranker_model=reranker_model,
                save_to_db=True,
                notes=label_note,
            )
            mode_summaries.append(summary)
            all_mode_items[summary.mode] = items

            print(
                f"    [Overall] Hit@1: {summary.overall.hit_at_1:.2f} | Hit@3: {summary.overall.hit_at_3:.2f} | "
                f"Hit@5: {summary.overall.hit_at_5:.2f} | MRR: {summary.overall.mrr:.3f} | Latency: {summary.overall.avg_latency_ms:.1f}ms"
            )
            print(
                f"    [Single]  Hit@5: {summary.single.hit_at_5:.2f} | MRR: {summary.single.mrr:.3f} (n={summary.single.total_questions})"
            )
            print(
                f"    [Paraphr] Hit@5: {summary.paraphrased.hit_at_5:.2f} | MRR: {summary.paraphrased.mrr:.3f} (n={summary.paraphrased.total_questions})"
            )
            print(
                f"    [Compound] Hit@5: {summary.compound.hit_at_5:.2f} | MRR: {summary.compound.mrr:.3f} (n={summary.compound.total_questions})"
            )

        # 2. Grounded Answer Synthesis Evaluation (--with-answers)
        answers_summary: Optional[AnswersEvalSummary] = None
        if args.with_answers:
            print("\n" + "=" * 80)
            print(f"STARTING GROUNDED ANSWER EVALUATION (--with-answers, n={args.sample_size})")
            print("=" * 80)
            answers_summary = run_answers_evaluation(
                db=db,
                questions=questions,
                sample_size=args.sample_size,
                mode="hybrid_rerank",
                delay_sec=1.0,
            )
            print(f"--> Evaluated {answers_summary.total_evaluated} answers:")
            print(f"    - Citation inclusion rate: {answers_summary.citation_inclusion_rate * 100:.1f}%")
            print(f"    - Cited source term overlap: {answers_summary.key_term_overlap_rate * 100:.1f}%")
            print(f"    - Wrong 'not found' refusals: {answers_summary.wrong_not_found_count} ({answers_summary.wrong_not_found_rate * 100:.1f}%)")
            print(f"    - Average generation latency: {answers_summary.avg_generation_ms:.1f} ms")

        # 3. Clinical Extraction Evaluation (--with-extraction)
        extraction_summary: Optional[ExtractionEvalSummary] = None
        if args.with_extraction:
            print("\n" + "=" * 80)
            print("STARTING CLINICAL EXTRACTION EVALUATION (--with-extraction)")
            print("=" * 80)
            extraction_summary = run_extraction_evaluation()
            print(f"--> Evaluated {extraction_summary.total_reports} synthetic reports:")
            for field, acc in extraction_summary.field_accuracy.items():
                print(f"    - {field:<18}: {acc * 100:.1f}%")
            print(f"    - Overall field accuracy: {extraction_summary.overall_field_accuracy * 100:.1f}%")
            print(f"    - Rule Validation Precision: {extraction_summary.validation_precision * 100:.1f}%")
            print(f"    - Rule Validation Recall   : {extraction_summary.validation_recall * 100:.1f}%")
            print(f"    - Rule Validation F1       : {extraction_summary.validation_f1:.3f}")

        # 4. Identify 10 Worst-Performing Questions
        worst_questions = identify_worst_questions(all_mode_items, limit=10)

        # 5. Generate and write EVAL_RESULTS.md
        out_path = Path(args.output)
        generate_evaluation_markdown(
            mode_summaries=mode_summaries,
            worst_questions=worst_questions,
            answers_summary=answers_summary,
            extraction_summary=extraction_summary,
            output_path=out_path,
        )

        print("\n" + "=" * 80)
        print(f"EVALUATION HARNESS COMPLETE. Results written to: {out_path}")
        print("=" * 80 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
