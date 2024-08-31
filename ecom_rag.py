import os
import numpy as np
import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

import torch
class DialogueTemplate():
    system_token = "<|system|>" #system prompt
    user_token = "<|user|>"
    assistant_token = "<|assistant|>"
    end_token = "<|end|>"

    messages = []

    # def __init__(self, tokenizer):
    #     self.tokenizer = tokenizer

    def get_special_tokens(self):
        return [self.system_token,self.user_token, self.assistant_token, self.end_token]

    # system_token: system_prompt <end>
    # user_token: user_msg_1 <end>
    # assistant model_ans_1 <end>
    # user........
    # <|assistant|> for inference (add during inference so model pretends to be an assistant)

    def get_training_prompt(self, infer = False):
        keys = ["product_name","price","warranty","refundable", "inventory","dimensions","reviews", "description"]
        # keys = ["order_status","product_name","refundable","days_since_ordered"]
        sys_string = ""
        for key in keys:
          if key in self.message.keys() and len(str(self.message[key])) > 0:
            sys_string += key + ": " + str(self.message[key]) + "\n"
          # else:
            # sys_string += key + ': ""\n'
        prompt = self.system_token + "\n" + sys_string  + self.end_token + "\n"
        prompt += self.user_token + "\n" + self.message["user_question"] + self.end_token + "\n"
        try:
            prompt += self.assistant_token + "\n" + self.message["support_answer"] + self.end_token + "\n"
        except:
            pass
            # elif message["role"] == "system":
            #     prompt += self.system_token + "\n" + message["value"] + self.end_token + "\n"
        if infer == False:
          prompt += '<|endoftext|>'
        # prompt = prompt +  ' <|endoftext|>'
        return prompt #fully formed tranining prompt

    def get_inference_prompt(self):
        prompt = self.get_training_prompt(infer=True)
        prompt += self.assistant_token
        return prompt

    def get_raw_dialogue(self):
        prompt = ''
        for message in self.messages:
            prompt += message["content"] + '\n'

        return prompt

    def prepare_dialogue(self, example):
        if 'content' in example.keys() and example['content'] is not None:
            self.messages = example['content']
        else:
            # print("Invalid conversations")
            pass

        self.message = example

        example['text'] = self.get_training_prompt()
        return example

def get_dialogue_template():
    return DialogueTemplate()

# examples = {
#         "product_name":"Compact Microwave",
#         "price":"",
#         "warranty":"",
#         "refundable":"returnable within 20 days",
#         "inventory":"",
#         "dimensions":"",
#         "reviews":"",
#         "description":"",
#         "user_question":"I'd like to cancel my compact microwave order that was placed a while ago. Can you assist?",
#         "support_answer":"The order is within the 20-day return period. I'll proceed with the cancellation now. cancel_order('Compact Microwave')",
#         "order_status":"ordered",
#         "days_since_ordered":10.0
#     }
# dialogue_template = get_dialogue_template()
# dialogue_template.message = examples
# print("Training:",dialogue_template.get_training_prompt())
# print("Infering:", dialogue_template.get_inference_prompt())

import os
import json
import torch
from torch.utils.data import DataLoader, random_split
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from transformers import AutoModelForCausalLM, AutoTokenizer, get_linear_schedule_with_warmup
from tqdm import tqdm

modelname = r"ecom_bot_prod"
model_username = r"ecom_bot_user"

model = AutoModelForCausalLM.from_pretrained(modelname).to("cuda")
tokenizer = AutoTokenizer.from_pretrained(modelname)

model_user = AutoModelForCausalLM.from_pretrained(model_username).to("cuda")
tokenizer_user = AutoTokenizer.from_pretrained(model_username)

print("Loaded prod bot")

search_tags = ['description', 'product_name']

class data_rag:
    def __init__(self, table, table_user):
        self.table = table #csv or json
        self.table_user = table_user

        # self.table.drop('support_answer',inplace=True, axis='columns')
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.doc_embeddings = [
            self.model.encode(f"{row['product_name']} {row['description']}")
            for _, row in table.iterrows()
        ]

        self.user_embeddings = [
            self.model.encode(f"{row['product_name']}")
            for _, row in table_user.iterrows()
        ]

    def search(self, query):
        query_embedding = self.model.encode([query])
        # Find similar documents
        similarities = cosine_similarity(query_embedding, self.doc_embeddings)[0]
        top_indices = similarities.argsort()[-5:][::-1]  # Get top 5 matches
        context = []
        # Context for generation
        # print(list(self.table.iloc[i] for i in top_indices))
        return list(self.table.iloc[i] for i in top_indices)[0]
        # print(f"Search: {query} Result: {context}")

    def search_user(self, query):
        query_embedding = self.model.encode([query])
        # Find similar documents
        similarities = cosine_similarity(query_embedding, self.user_embeddings)[0]
        top_indices = similarities.argsort()[-5:][::-1]  # Get top 5 matches
        context = []
        # Context for generation
        # print(list(self.table.iloc[i] for i in top_indices))
        return list(self.table_user.iloc[i] for i in top_indices)[0]
        # print(f"Search: {query} Result: {context}")

df = pd.read_json('assets/products.json')
df_user = pd.read_json('assets/user.json')
print(df.head(5))

erag = data_rag(df,df_user)

def prod_inference(prompt,max_new_tokens=128, temperature=0.3, top_k=100,top_p=0.95, additional_context=None):
    model.eval()
    dialogue_template = get_dialogue_template()
    device = "cuda"
    
    if additional_context is not None:
        additional_context = str(additional_context).strip()
        # print("Additional context is:",additional_context) 
        sys_search = erag.search(prompt + str(additional_context))
    else:
        sys_search = erag.search(prompt)
    print("Searching result:", sys_search)
    sys_search['user_question'] = prompt
    dialogue_template.message = sys_search
    input_text = dialogue_template.get_inference_prompt()
    # print("the input prompt is: ", input_text)
    inputs = tokenizer(input_text, return_tensors="pt",padding=True, truncation=True,max_length=1024).to(device)
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)
    output = model.generate(
        input_ids,
        attention_mask=attention_mask,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id
    )

    generated_text = tokenizer.decode(output[0], skip_special_tokens=False)
    # return generated_text
    response = generated_text.split(dialogue_template.assistant_token)[1].strip()
    response = response.replace(dialogue_template.end_token, "").strip()
    response = response.replace("<|endoftext|>", "").strip()
    return response

def user_inference(prompt,max_new_tokens=128, temperature=0.3, top_k=100,top_p=0.95, additional_context=None):
    model.eval()
    dialogue_template = get_dialogue_template()
    device = "cuda"
    
    if additional_context is not None:
        additional_context = str(additional_context).strip()
        # print("Additional context is:",additional_context) 
        sys_search = erag.search_user(prompt + str(additional_context))
    else:
        sys_search = erag.search_user(prompt)
    print("Searching result:", sys_search)
    sys_search['user_question'] = prompt
    dialogue_template.message = sys_search
    input_text = dialogue_template.get_inference_prompt()
    # print("the input prompt is: ", input_text)
    inputs = tokenizer_user(input_text, return_tensors="pt",padding=True, truncation=True,max_length=1024).to(device)
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)
    output = model_user.generate(
        input_ids,
        attention_mask=attention_mask,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id
    )

    generated_text = tokenizer_user.decode(output[0], skip_special_tokens=False)
    # return generated_text
    response = generated_text.split(dialogue_template.assistant_token)[1].strip()
    response = response.replace(dialogue_template.end_token, "").strip()
    response = response.replace("<|endoftext|>", "").strip()
    return response

# if __name__ == "__main__":

#     # erag.search("How much does the logitech mouse cost")
#     while True:
#         search_term = input("Enter the query:\n")
#         prompts = ["What is the cost of the fancy house plant?","Is it better indoor or outdoor?", "How much water does the plant need?", "Can it grow without soil?", "Does this plant need light?", "How many of these plants are in inventory?", "Is the pot self watering?"]
#         # for prompt in prompts:
#         # print(prompt)
#         # q = {
#         #         "product_name": "Fancy house plant",
#         #         "price": "$2989.99",
#         #         "warranty": "3-month warranty",
#         #         "refundable": "Yes, within 144 days",
#         #         "inventory": 940,
#         #         "dimensions": "10x12 inches",
#         #         "reviews": "4.9 stars (50 reviews)",
#         #         "description": "Money plant is an excellent indoor plant due to its ability to survive in low light . It is an Air Purifier plant as it efficiently removes indoor pollutants. It is also an easy to care for plant suitable in living room, balcony, bedroom or in hanging baskets. This plant with its beautiful heart shaped leaves with specles of cream or white markings is believed to bring good luck & prosperity to your home according to Feng Shui. Watering requirement for the plant is generally twice a week. But it is ideal to water it whenever the top layer of the soil feels dry. Pot is self watering where excess water gets stored in the reservoir below, the roots then absorbs water via capillary action and the plants get water as and when required, allowing you to water less frequently. Making it perfect plant for office desk.",
#         #         "user_question": prompt
#         # }
#         generated_text = prod_inference(search_term,top_k=50,temperature=0.3,top_p=1.0,max_new_tokens=256)
#         print(f"{generated_text}")
        # erag.search(search_term)



