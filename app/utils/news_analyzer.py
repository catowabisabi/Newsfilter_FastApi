"""
新聞分析器 - 關鍵字評分系統
"""

import re
from typing import Dict, Any, List, Set


class NewsAnalyzer:
    """新聞關鍵字分析器"""
    
    def __init__(self):
        self.keywords = {
            4: ["Endpoints", "Endpoint", "Designation", "Breakthrough", "Pivotal", "Revolutionary"],
            3: ["Phase III", "Positive", "Top-Line", "Significant", "Demonstrates", "Treatment", 
                "Drug Trials", "Agreement", "Cancer", "Partnership", "Collaboration", "Improvements", 
                "Successful", "Billionaire", "Carl Icahn", "Increase", "Awarded", "Primary", 
                "Milestone", "Surge", "Record", "Approval Process", "Regulatory", "Clearance"],
            2: ["Phase II", "Receives", "FDA", "Approval", "Benefits", "Benefit", "Beneficial", 
                "Fast Track", "Breakout", "Acquires", "Acquire", "Acquisition", "Expand", 
                "Expansion", "Contract", "Completes", "Promising", "Achieves", "Achieve", 
                "Achievements", "Achievement", "Launches", "Enhancement", "Innovation", 
                "Clinical Trial", "Pipeline", "Success", "Funding", "Grant"],
            1: ["Phase I", "Grants", "Investors", "Accepted", "New", "Signs", "Merger", "Gain", 
                "Initiates", "Starts", "Begins", "Preliminary", "Early Stage", "Development", 
                "Prospects", "Proposal", "Investor Meeting"]
        }
    
    def analyze(self, title: str, content: str) -> Dict[str, Any]:
        """分析新聞文本並返回評分和關鍵字"""
        combined_text = f"{title} {content}"
        return self._analyze_text(combined_text)
    
    def _analyze_text(self, content: str) -> Dict[str, Any]:
        """分析文本內容"""
        score = 0
        important_keywords: Set[str] = set()
        
        for points, words in self.keywords.items():
            for word in words:
                if re.search(rf"\b{re.escape(word)}\b", content, re.IGNORECASE):
                    score += points
                    important_keywords.add(word)
        
        return {
            "score": score,
            "important_keywords": list(important_keywords)
        }
