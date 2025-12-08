from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, auth
import os
import sqlite3
from dotenv import load_dotenv

if not load_dotenv('.env.local'):
	load_dotenv('.env')

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
auth_app = firebase_admin.initialize_app(cred)
db = sqlite3.connect(os.getenv("BACKEND_DB"), check_same_thread=False)

app = FastAPI()
security = HTTPBearer()

origins = [
	"http://localhost",
	"http://localhost:5173",
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
	
	print("Adding bookmark for user:", user['uid'], bookmark)
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
	print("Fetching bookmarks for user:", user['uid'])
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
	print("Deleting bookmark for user:", user['uid'], "bookmark_id:", bookmark_id)
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
	print("Counting bookmarks for user:", user['uid'])
	cursor = db.execute('''
		SELECT COUNT(*)
		FROM bookmarks
		WHERE uid = ?
	''', (user['uid'],))
	count = cursor.fetchone()[0]
	return {"count": count}

@app.get("/api/v1/health")
async def health_check():
	return {"status": "ok"}