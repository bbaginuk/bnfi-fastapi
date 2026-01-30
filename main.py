from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymysql
import os

app = FastAPI()

# =========================
# DB 연결 함수
# =========================
def get_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),   # testdb
        port=3306,
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ssl": {}}                  # Azure MySQL 필수
    )

# =========================
# 앱 시작 시 테이블 자동 생성
# =========================
@app.on_event("startup")
def init_db():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    finally:
        conn.close()

# =========================
# 헬스 체크
# =========================
@app.get("/api/health")
def health():
    try:
        conn = get_conn()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# READ
# =========================
@app.get("/api/users")
def get_users():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users ORDER BY id DESC")
            return cur.fetchall()
    finally:
        conn.close()

# =========================
# CREATE 입력 모델
# =========================
class UserCreate(BaseModel):
    name: str
    email: str

# =========================
# CREATE
# =========================
@app.post("/api/users")
def create_user(user: UserCreate):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                (user.name, user.email)
            )
            conn.commit()
            return {"result": "created"}
    finally:
        conn.close()

# =========================
# UPDATE
# =========================
@app.put("/api/users/{user_id}")
def update_user(user_id: int, user: UserCreate):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET name = %s, email = %s
                WHERE id = %s
                """,
                (user.name, user.email, user_id)
            )
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
            return {"result": "updated"}
    finally:
        conn.close()

# =========================
# DELETE
# =========================
@app.delete("/api/users/{user_id}")
def delete_user(user_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
            return {"result": "deleted"}
    finally:
        conn.close()
