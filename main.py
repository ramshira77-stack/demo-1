import os 
import requests
from bs4 import BeautifulSoup
from config import settings
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from database import engine, users, messages

#langchain imports
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from duckduckgo_search import DDGS

os.environ['GROQ_API_KEY'] = settings.groq_api_key

app = FastAPI()

#--- Tools ---

def search_web(query: str) -> str:
    '''search the web using DuckDuckGo and return the top result as string.'''
    with DDGS() as ddgs:
        return "\n".join([r['body'] for r in ddgs.text(query, max_results=3)])
    
def scrap_web(url: str) -> str:
    '''scrap the content of a web page and return it as a string.'''
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for s in soup(['script', 'style']):
        s.extract()
    return soup.get_text()[:2000] # Limit to 2000 character to avoid overloading

#--- database dependencies ---
def get_db():
    with Session(engine) as session:
        yield session

#---LLM Setup---
model = ChatGroq(model="openai/gpt-oss-20b", temperature=0.7)

#--- langchain workflow ---
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that can answer questions based on the provided context."),
    ("human", "Answer the questions {input}"),
    MessagesPlaceholder(variable_name="history")
])

chain = prompt | model | StrOutputParser()

#--- API routes ---
class UserSchema(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str


#--- API routes ---

@app.post("/register")
def register(user: UserSchema, db: Session = Depends(get_db)):
    existing_user = db.exec(select(users).where(users.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=400 , detail="Username already exists")
    new_user = users(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.u_id}

@app.post("/{username}/chat")
def chat(username: str, chat_request: ChatRequest, db: Session = Depends(get_db)):
    user = db.exec(select(users).where(users.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
   
    history = []
    statment = select(messages).where(messages.u_id == user.u_id).order_by(messages.timestamp)
    chat_history = db.exec(statment).all()

    for msg in chat_history:
        if msg.role == "user":
            history.append(HumanMessage(content=msg.content))
        else:
            history.append(AIMessage(content=msg.content))

    user_message = chat_request.message

    if 'search' in user_message.lower():
        tool_output = search_web(user_message)
        user_message += f"\n\n Web search results :\n{tool_output}"
    response = chain.invoke({"input": user_message, "history": history[-4:]}) # Use last 4 messages for context

    db.add(messages(u_id = user.u_id , role = 'user' , content = user_message))
    db.add(messages(u_id = user.u_id , role = 'assistant' , content = response))
    db.commit()

    return {"response": response}