import requests
import re
import textstat
import math
from google.cloud import language_v2
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'seo-manager-460500-774345dbfb0f.json'
nlp_client = language_v2.LanguageServiceClient()
API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
TIMEOUT = int(os.getenv("TIMEOUT"))


class llm_app:
    def __init__(self, input):
        self.API_BASE_URL = API_BASE_URL
        self.headers = {
                    "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
        }
        self.conversation = []
        self.input = input
        
    def get_data_from_api(self, payload):
        try:
            response = requests.post(
            self.API_BASE_URL,
            headers=self.headers,
            json=payload,
            timeout=TIMEOUT
            )
            if response.ok:
                return response.json()
            else:
                return {"error": response.status_code}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
            
    def ask_openrouter(self,message):
        data = {
                "model": MODEL,  
                "messages": [{"role": "user", "content": message}],
                "temperature": 0.7,
            }

        #response = requests.post(API_URL, headers=headers, json=data)
        response= self.get_data_from_api(data)

        if "error" in response:
            return f"Error: {response.get('message', response['error'])}"
        return response["choices"][0]["message"]["content"]
        
    def chat(self):
        print("🤖 AI Assistant (powered by OpenRouter). Type 'exit' to quit.")
        user_input = self.input 
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
        reply = self.ask_openrouter(user_input)
        self.conversation.append((user_input, reply))
        print("AI:", reply)
        return reply
            
    


class ReadabilityAnalyzer:
    def __init__(self, text):
        self.text = text
        
    def get_grade(self):
        grade_level = [math.ceil(textstat.flesch_kincaid_grade(self.text)),
                        math.ceil(textstat.flesch_reading_ease(self.text)),
                        math.ceil(textstat.smog_index(self.text)),
                        math.ceil(textstat.coleman_liau_index(self.text)),
                        math.ceil(textstat.automated_readability_index(self.text)),
                        math.ceil(textstat.dale_chall_readability_score(self.text)),
                        math.ceil(textstat.difficult_words(self.text)),
                        math.ceil(textstat.linsear_write_formula(self.text)),
                        textstat.text_standard(self.text)]
        return grade_level
        
    # def get_moderation(self):
    #     """"
    #     Maps model output labels to custom moderation categories.
    #     """
    #     label_map = {
    #             "toxicity": "Toxic",
    #             "severe_toxicity": "Violent",
    #             "obscene": "Sexual Contains",
    #             "identity_attack": "Derogatory",
    #             "insult": "Insult",
    #             "threat": "Death / Harm & Tragedy",
    #             "sexual_explicit": "Sexual Contains"
    #     }

    #     results = set()
    #     for result in modaration(self.text[0]):
    #         if result['score'] > 0.5:  # confidence threshold
    #             mapped_label = label_map.get(result['label'], None)
    #             if mapped_label:
    #                 results.add(mapped_label)

    #     return list(results)
    
    def get_sentiment(self):
        if self.text:
            overall = []
            sentence_wise=[]
            sentiment={}
            document = language_v2.Document(content=self.text, type_= language_v2.Document.Type.PLAIN_TEXT,language_code='en')
            response = nlp_client.analyze_sentiment(request={"document": document})
            sentiment = response.document_sentiment
            sentiment= {
                "score": sentiment.score,
                "magnitude": sentiment.magnitude
            }
            overall.append(sentiment)

            parts = re.split(r'[.;?]', self.text)
            parts = [part.strip() for part in parts if part.strip()]    
            for part in parts:
                sentiment={}
                document = language_v2.Document(content=part, type_= language_v2.Document.Type.PLAIN_TEXT,language_code='en')
                response = nlp_client.analyze_sentiment(request={"document": document})
                sentiment = response.document_sentiment
                sentiment= {
                    "part": part,
                    "scores":{
                        "score": sentiment.score,
                        "magnitude": sentiment.magnitude
                    }
                }
                sentence_wise.append(sentiment)

            return(overall,sentence_wise)

        else:
            return "No text to analyze"
        

    def detect_genre(self):
        if self.text:
            document = language_v2.Document(content=self.text, type_= language_v2.Document.Type.PLAIN_TEXT,language_code='en')
            response = nlp_client.classify_text(request={"document": document})
            return [(category.name, category.confidence) for category in response.categories]
        else:
            return "No text to analyze"
        
    def get_ner(self):
        if self.text:
            document = language_v2.Document(content=self.text, type_=language_v2.Document.Type.PLAIN_TEXT,language_code='en')
            response = nlp_client.analyze_entities(request={"document": document})
            entities = [(entity.name, language_v2.Entity.Type(entity.type_).name) for entity in response.entities]
            return entities
        else:
            return "No text to analyze"
        



if __name__=='__main__':
    promt = "write me about gteat Indian king Ashoka."
    llm = llm_app(promt)
    chat=llm.chat()
    print(chat)
    read = ReadabilityAnalyzer(chat)
    print(f'The grade of the response: {read.get_grade()}')
    print('--------------------------------------------------------')
    print(f'The Sentiment of the response: {read.get_sentiment()}')
    print('--------------------------------------------------------')
    print(f'The genre of the response: {read.detect_genre()}')
    print('--------------------------------------------------------')
    print(f'The list of NER of the response: {read.get_ner()}')
    print('--------------------------------------------------------')




    
