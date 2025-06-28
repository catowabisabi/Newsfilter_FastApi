import re
from datetime import datetime
from utils.translator import CnTranslator


class NewsAnalyzer:
    def __init__(self):
        """ self.keywords = {
            4: ["Endpoints", "Endpoint", "Designation"],
            3: ["Phase III", "Positive", "Top-Line", "Significant", "Demonstrates", "Treatment", "Drug Trials", 
                "Agreement", "Cancer", "Partnership", "Collaboration", "Improvements", "Successful", "Billionaire", 
                "Carl Ichan", "Increase", "Awarded", "Primary"],
            2: ["Phase II", "Receives", "FDA", "Approval", "Benefits", "Benefit","Beneficial", "Fast Track", "Breakout", 
                "Acquires", "Acquire", "Acquisition", "Expand", "Expansion", "Contract", "Completes", "Promising", "Achieves", "Achieve", 
                "Achievements", "Achievement", "Launches"],
            1: ["Phase I", "Grants", "Any Large Sum of $", "Investors", "Accepted", "New", "Signs", "Merger", "Gain"]
        } """

        self.keywords = {
            4: ["Endpoints", "Endpoint", "Designation"],
            3: ["Phase III", "Positive", "Top-Line", "Significant", "Demonstrates", "Treatment", "Drug Trials", 
                "Agreement", "Cancer", "Partnership", "Collaboration", "Improvements", "Successful", "Billionaire", 
                "Carl Ichan", "Increase", "Awarded", "Primary"],
            2: ["Phase II", "Receives", "FDA", "Approval", "Benefits", "Benefit","Beneficial", "Fast Track", "Breakout", 
                "Acquires", "Acquire", "Acquisition", "Expand", "Expansion", "Contract", "Completes", "Promising", "Achieves", "Achieve", 
                "Achievements", "Achievement", "Launches"],
            1: ["Phase I", "Grants", "Any Large Sum of $", "Investors", "Accepted", "New", "Signs", "Merger", "Gain"]
        }
    
    

    def analyze(self, title, content):         
        combined_text = f"{title} {content}"
        result = self.analyze_text(combined_text)
        return result
    
    def analyze_text(self, content, show_result = False):
        score = 0
        important_keywords = set()
        for points, words in self.keywords.items():
            for word in words:
                if re.search(rf"\b{word}\b", content, re.IGNORECASE):
                    score += points
                    important_keywords.add(word)

        result = {
            "score": score,
            "important_keywords": list(important_keywords)
        }

        if show_result:
            print("\n新聞分數:", score)
            print("關鍵字:", ", ".join(important_keywords))
            print("")

        return result
    

    def get_result(self, title, summary):
        self.title = title
        self.summary = summary

        print (type(self.title))
        print (type(self.summary))
        print (type(self.keywords))
        analyed_result = self.analyze(self.title, self.summary)
        self.score = analyed_result["score"]
        self.this_keywords = analyed_result["important_keywords"]
        cn_translator = CnTranslator()
        self.title_cn = cn_translator.translate_to_chinese(self.title)
        self.summary_cn = cn_translator.translate_to_chinese(self.summary)

        return {
            "title":self.title ,
            "summary":self.summary,
       
            "score":self.score,
            "keywords":self.this_keywords,
    
            "title_cn":self.title_cn,
            "summary_cn":self.summary_cn
        }



#self.news_analyzer  = NewsAnalyzer()