"""
AGH Knowledge Graph Alignment & Cross-Validation Engine.
Links Academic papers with corresponding GitHub codebases and HuggingFace models.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from ..ingestion.collector import RawInsightItem


@dataclass
class AlignedInsightNode:
    paper_title: str
    paper_author: str
    journal: str
    github_repo_url: Optional[str]
    hf_model_id: Optional[str]
    has_full_evidence_chain: bool
    relevance_score: float                # 0-10 分
    domain_tags: list
    raw_item: RawInsightItem


class GraphAlignmentEngine:
    """
    Evaluates correlation between academic papers, engineering code, and open-weights models.
    """
    def align_item(self, item: RawInsightItem) -> AlignedInsightNode:
        text = (item.title + " " + item.summary + " " + str(item.metadata)).lower()
        
        # 计算量化资管相关性打分
        score = 0.0
        if any(k in text for k in ["定价", "收益率", "alpha", "对冲", "因子", "期权", "转债"]):
            score += 4.5
        if any(k in text for k in ["实证", "多空", "预测", "sharpe", "波动率"]):
            score += 3.5
        if item.source_type == "academic":
            score += 1.5
            
        score = min(score, 10.0)
        
        github_url = item.metadata.get("matched_github_repo")
        has_full_chain = bool(github_url)
        
        return AlignedInsightNode(
            paper_title=item.title,
            paper_author=item.author_or_owner,
            journal=item.metadata.get("journal", "Academic Journal"),
            github_repo_url=github_url,
            hf_model_id=item.metadata.get("hf_model_id"),
            has_full_evidence_chain=has_full_chain,
            relevance_score=score,
            domain_tags=["Convertible_Bond", "Option_Pricing", "Hedging_Alpha", "China_A_Share"],
            raw_item=item
        )
