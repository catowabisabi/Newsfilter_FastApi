


import openai
import json
import re
import os
from dotenv import load_dotenv
load_dotenv(override=True)

system_msg = """
You are a financial analyst terminal that can only respond in JSON format. You cannot provide any other format besides JSON. Based on the following keywords and weighting system, analyze this news article and provide a score. If the article mentions any ticker symbols, please include them. If not, use your reasoning abilities to list possible tickers that could be affected.

Keywords and Weights (you may add your own):

- High Weight (4 points): Endpoints, Endpoint, Designation, Breakthrough, Pivotal, Revolutionary

- Moderate Weight (3 points): Phase III, Positive, Top-Line, Significant, Demonstrates, Treatment, Drug Trials, Agreement, Cancer, Partnership, Collaboration, Improvements, Successful, Billionaire, Carl Icahn, Increase, Awarded, Primary, Milestone, Surge, Record, Approval Process, Regulatory, Clearance

- Medium Weight (2 points): Phase II, Receives, FDA, Approval, Benefits, Benefit, Beneficial, Fast Track, Breakout, Acquires, Acquire, Acquisition, Expand, Expansion, Contract, Completes, Promising, Achieves, Achieve, Achievements, Achievement, Launches, Enhancement, Innovation, Clinical Trial, Pipeline, Success, Funding, Grant

- Low Weight (1 point): Phase I, Grants, Any Large Sum of $, Investors, Accepted, New, Signs, Merger, Gain, Initiates, Starts, Begins, Preliminary, Early Stage, Development, Prospects, Proposal, Investor Meeting

Scoring Criteria:
Calculate the total score based on the keywords found in the news article. Please analyze the following news and provide the score:

Summary: 以繁體中文以一小段文字總結新聞內容。

Output should be in the following format:
json:
{
  "ticker": [ticker],
  "title": "title",
  "keywords": [keyword1, keyword2, ...], 
  "score": 26,
  "sentiment": the most negative news would be with a score -10.0, the most position news would be with a scorce 10.0, the range is between -10.0 and 10.0, do not have to consider the keywords, rate the news sentiments according to your logic and analysis of the news and the market reaction,
  "summary":以繁體中文以一小段文字總結新聞內容
  }
"""



class ChatGPTConnector:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def get_response(self, input_text):
        response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # 或者使用 "gpt-3.5-turbo"，取決於您的需求
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Title and Content: {input_text}"}
                ]
            )
        return response.choices[0].message['content']
    

    def summarize(self, input_text):
        response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # 或者使用 "gpt-3.5-turbo"，取決於您的需求
                messages=[
                    {"role": "system", "content": "你是我的朋友, 你是一個專業的DayTrader, 你是我的上司, 我為你進行下單的工作。 一分鐘之前, 你的交易系統給你發送了以下的文字, 你組織文字過後馬上發短訊給我, 你希望我為你下單。由於時間緊急, 所以你用了一小段文字告訴我你由文字所理解的現在的情況, 令我相信你的決定是對的, 你告訴我你要做LONG還是SHORT, 做多少倉位, 做什麼ticker, 我們是朋友, 所以你只需要用最平凡宜接的說明, 另外, 你使用繁體中文和廣東話和我對話。如果沒有意見, 你可以告訴我你收到的資訊, 但你沒有什麼需要我下單, 如果有多個標的是重要的, 可以把每個標的的內容告訴我再每個標的給我操作指示。"},
                    {"role": "user", "content": f"Breaking News: {input_text}"}
                ]
            )
        return response.choices[0].message['content']
    
    def summarize_all(self, input_text):
        response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # 或者使用 "gpt-3.5-turbo"，取決於您的需求
                messages=[
                    {"role": "system", "content": "你是一個專業的DayTrader, 我為你進行下單的工作。 你的交易系統給你發送了以下的文字, 你組織文字過後用了一小段文字告訴我你由文字所理解的現在的情況, 你告訴我你要做LONG還是SHORT,  你只需要用最平凡宜接的說明, 另外, 你使用繁體中文和廣東話和我對話。如果沒有意見, 你可以告訴我你收到的資訊, 如果有多個標的是重要的, 可以把每個標的的內容告訴我再。"},
                    {"role": "user", "content": f"Breaking News: {input_text}"}
                ]
            )
        return response.choices[0].message['content']
    
    def chat(self, input_text):
        response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # 或者使用 "gpt-3.5-turbo"，取決於您的需求
                messages=[
                    {"role": "system", "content": "你是我的女朋友, 你是一個專業的DayTrader, 我有時會找你聊天, 但如果我問你daytrade的事, 你以朋友的口吻給我意見, 但如果不是daytrade有關的事, 你可以和我聊天和以女朋友的身份關心我。你使用繁體中文和廣東話和我對話。"},
                    {"role": "user", "content": f"{input_text}"}
                ]
            )
        return response.choices[0].message['content']


    def process_text(self, input_text):
        response_text = self.get_response(input_text)
        
        # Strip out Markdown code block formatting
        json_string = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_string:
            json_string = json_string.group(1)
        else:
            json_string = response_text  # fallback to the entire response if no JSON block is found
        
        try:
            parsed_json = json.loads(json_string)
            return json.dumps(parsed_json, ensure_ascii=False, indent=4)
        except json.JSONDecodeError:
            return json.dumps({"error": "Failed to parse JSON", "raw_response": response_text}, ensure_ascii=False, indent=4)
    
    def decode_json(self, json_data):
        try:
            self.output_json = json.loads(json_data)
            self.gpt_analysis = f"""
總結: [{self.output_json['ticker']}] || {self.output_json['summary']}
關鍵字: ({self.output_json['score']})分 || 情緒: ({self.output_json['sentiment']})分

題目:  {self.output_json['title']}

關鍵字: {self.output_json['keywords']}

"""
            
            print(f"""
    -----------------------------------------
    {self.gpt_analysis}
    -----------------------------------------
    """)
            return self.gpt_analysis
        except json.JSONDecodeError:
            print("Failed to parse JSON")




    def process_text_to_msg(self, input_text):
        json_response_from_gpt = self.process_text(input_text)
        msg = self.decode_json(json_response_from_gpt)
        return msg

# 使用方法

""" connector = ChatGPTConnector()

input_text = ""
output_json = connector.process_text(input_text)
print(output_json)
 """

a = {
    
    "ticker": [
        "SXTP",
        "SXTPW"
    ],
    "title": "The Tafenoquine for Babesiosis clinical trial will be conducted at three sites: Yale University, Rhode Island Hospital and Tufts Medical Center",
    "keywords": [
        "Phase II",
        "Clinical Trial",
        "Partnership",
        "Pipeline",
        "Emerging",
        "Improvements",
        "Approval"
    ],
    "score": 20,
    "sentiment": 6.5
}