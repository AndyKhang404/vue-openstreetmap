from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, auth
import os
import sqlite3
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime, timedelta
import re

if not load_dotenv('.env.local'):
	load_dotenv('.env')

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
auth_app = firebase_admin.initialize_app(cred)
db = sqlite3.connect(os.getenv("BACKEND_DB"), check_same_thread=False)

app = FastAPI()
security = HTTPBearer()
hf_client = InferenceClient(
	api_key=os.getenv("HF_TOKEN"),
)

origins = [
	"http://localhost",
	"http://localhost:5173",
	# Add more origins as needed
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(_: FastAPI):
	yield
	db.close()

@app.get("/api/v1/health")
async def health_check():
	return {"status": "ok"}

class Bookmark(BaseModel):
	lat: float
	lon: float
	type: str
	name: str | None = None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # Verify the token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

@app.post("/api/v1/user/bookmarks")
async def add_bookmark(bookmark: Bookmark, user: dict = Depends(get_current_user)):
	# Maximum 20 bookmarks per user
	cursor = db.execute('''
		SELECT COUNT(*)
		FROM bookmarks
		WHERE uid = ?
	''', (user['uid'],))
	count = cursor.fetchone()[0]
	if count >= 20:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Maximum bookmark limit reached",
		)
	
	db.execute('''
		INSERT INTO bookmarks (uid, lat, lon, type, name)
		VALUES (?, ?, ?, ?, ?)
	''', (user['uid'], bookmark.lat, bookmark.lon, bookmark.type, bookmark.name))
	db.commit()
	return {
            "message": "Bookmark added successfully", 
            "bookmark_id": db.execute('SELECT last_insert_rowid()').fetchone()[0]
    }

@app.get("/api/v1/user/bookmarks")
async def get_bookmarks(user: dict = Depends(get_current_user)):
	cursor = db.execute('''
		SELECT id, lat, lon, type, name
		FROM bookmarks
		WHERE uid = ?
	''', (user['uid'],))
	bookmarks = [
		{
			"id": row[0],
			"lat": row[1],
			"lon": row[2],
			"type": row[3],
			"name": row[4]
		}
		for row in cursor.fetchall()
	]
	return {"bookmarks": bookmarks}

@app.delete("/api/v1/user/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: int, user: dict = Depends(get_current_user)):
	cursor = db.execute('''
		DELETE FROM bookmarks
		WHERE id = ? AND uid = ?
	''', (bookmark_id, user['uid']))
	db.commit()
	if cursor.rowcount == 0:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Bookmark not found",
		)
	return {"message": "Bookmark deleted successfully"}

@app.get("/api/v1/user/bookmarks/count")
async def count_bookmarks(user: dict = Depends(get_current_user)):
	cursor = db.execute('''
		SELECT COUNT(*)
		FROM bookmarks
		WHERE uid = ?
	''', (user['uid'],))
	count = cursor.fetchone()[0]
	return {"count": count}

# Rate limiting store: {uid: [(timestamp1, timestamp2, ...)]}
chat_rate_limit = defaultdict(list)
CHAT_RATE_LIMIT = 10  # requests per minute
CHAT_WINDOW = 60  # seconds

def check_rate_limit(uid: str) -> bool:
	"""Check if user has exceeded rate limit"""
	now = datetime.now()
	cutoff = now - timedelta(seconds=CHAT_WINDOW)
	
	# Remove old timestamps
	chat_rate_limit[uid] = [ts for ts in chat_rate_limit[uid] if ts > cutoff]
	
	# Check if limit exceeded
	if len(chat_rate_limit[uid]) >= CHAT_RATE_LIMIT:
		return False
	
	# Add current timestamp
	chat_rate_limit[uid].append(now)
	return True

def validate_chat_messages(messages: list[dict]) -> tuple[bool, str]:
	"""Validate chat messages for safety and format"""
	if not messages:
		return False, "Messages cannot be empty"
	
	if len(messages) > 50:
		return False, "Too many messages in conversation"
	
	# Check for inappropriate content patterns
	inappropriate_patterns = [
		r'\b(hack|exploit|bypass|jailbreak)\b',
		r'\b(illegal|fraud|scam)\b',
	]
	
	for msg in messages:
		if not isinstance(msg, dict) or 'content' not in msg:
			return False, "Invalid message format"
		
		content = str(msg.get('content', '')).lower()
		
		# Check message length
		if len(content) > 5000:
			return False, "Message too long (max 5000 characters)"
		
		# Basic content filtering
		for pattern in inappropriate_patterns:
			if re.search(pattern, content, re.IGNORECASE):
				return False, "Message contains inappropriate content"
	
	return True, ""

@app.post("/api/v1/chat")
async def chat_endpoint(messages: list[dict], user: dict = Depends(get_current_user)):
	# Rate limiting
	if not check_rate_limit(user['uid']):
		raise HTTPException(
			status_code=status.HTTP_429_TOO_MANY_REQUESTS,
			detail=f"Rate limit exceeded. Maximum {CHAT_RATE_LIMIT} requests per minute.",
		)
	
	# Validate messages
	is_valid, error_msg = validate_chat_messages(messages)
	if not is_valid:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=error_msg,
		)
	
	try:
		completion = hf_client.chat.completions.create(
			model=os.getenv("HF_MODEL"),
			messages=messages,
			max_tokens=1000,  # Limit response length
		)
		return completion
	except Exception:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to process chat request",
		)