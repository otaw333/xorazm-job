from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import psycopg2
import os
from fastapi import WebSocket
from typing import Dict, List

app = FastAPI()
# ====== CORS ======
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====== MODELS ======
class UserLogin(BaseModel):
    email: str
    password: str



# ====== DB CONNECT ======


def get_db():
    conn = psycopg2.connect(os.getenv("postgresql://xorazm_job_db_user:LjQlwMjWeg67uemmDaYu6JfFq3B6icRA@dpg-d73tg4muk2gs739rct1g-a/xorazm_job_db"))
    return conn


# ==========================
# 🔹 HAMMA VAKANSIYALAR
# ==========================
@app.get("/jobs")
def get_jobs(
    search: Optional[str] = None,
    location: Optional[str] = None
):

    conn = get_db()
    cur = conn.cursor()

    try:

        query = """
            SELECT 
                j.id,
                j.title,
                j.company,
                j.salary,
                j.location,
                j.description,
                j.user_id,
                j.vacancies_count,
                j.experience_required,
                j.payment_type,
                j.employment_type,
                j.work_mode,
                j.work_time,
                j.education_level,
                j.university,
                j.faculty,
                j.edu_from,
                j.edu_to,
                j.gender,
                j.lat,
                j.lng,
                j.age_required,
                j.min_age,
                j.max_age,
                j.field,
                j.job_for,
                j.created_at,
                j.views_count,
                COUNT(a.id) as applications_count

            FROM jobs j

            LEFT JOIN applications a 
            ON j.id = a.job_id

            WHERE 1=1
        """

        params = []

        if search:
            query += " AND (LOWER(j.title) LIKE %s OR LOWER(j.company) LIKE %s)"
            params.extend([
                f"%{search.lower()}%",
                f"%{search.lower()}%"
            ])

        if location:
            query += " AND LOWER(j.location) LIKE %s"
            params.append(f"%{location.lower()}%")

        query += """
            GROUP BY 
                j.id, j.title, j.company, j.salary, j.location,
                j.description, j.user_id, j.vacancies_count,
                j.experience_required, j.payment_type,
                j.employment_type, j.work_mode, j.work_time,
                j.education_level, j.university, j.faculty,
                j.edu_from, j.edu_to, j.gender, j.lat, j.lng,
                j.age_required, j.min_age, j.max_age,
                j.field, j.job_for, j.created_at, j.views_count

            ORDER BY j.id DESC
        """

        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        result = []

        for r in rows:

            result.append({

                "id": r[0],
                "title": r[1],
                "company": r[2],
                "salary": r[3],
                "location": r[4],
                "desc": r[5],
                "user_id": r[6],
                "vacancies_count": r[7],
                "experience_required": r[8],
                "payment_type": r[9],
                "employment_type": r[10],
                "work_mode": r[11],
                "work_time": r[12],
                "education_level": r[13],
                "university": r[14],
                "faculty": r[15],
                "edu_from": r[16],
                "edu_to": r[17],
                "gender": r[18],
                "lat": float(r[19]) if r[19] else None,
                "lng": float(r[20]) if r[20] else None,
                "age_required": r[21],
                "min_age": r[22],
                "max_age": r[23],
                "field": r[24],
                "job_for": r[25],

                # statistika
                "created_at": r[26],
                "views_count": r[27],
                "applications_count": r[28]

            })

        return result

    finally:
        conn.close()

# ==========================
# 🔹 VAKANSIYA korishlar soni 
# ==========================

@app.post("/jobs/{job_id}/view")
def add_view(job_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE jobs
        SET views_count = views_count + 1
        WHERE id=%s
    """, (job_id,))

    conn.commit()
    conn.close()

    return {"message": "view added"}

# ==========================
# 🔹 BITTA VAKANSIYA
# ==========================
@app.get("/jobs/{job_id}")
def get_job(job_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
        id,
        title,
        company,
        salary,
        payment_type,
        location,
        description,
        user_id,
        views_count,
        created_at,
        (SELECT COUNT(*) FROM applications a WHERE a.job_id = jobs.id) AS applications_count,
                
        experience_required,
        employment_type,
        work_mode,
        work_time,

        education_level,
        gender,
        job_for,

        age_required,
        min_age,
        max_age,

        field,
        english_level,
        russian_level,
        lat,
        lng

        FROM jobs
        WHERE id=%s
    """, (job_id,))

    r = cur.fetchone()
    conn.close()

    if not r:
        raise HTTPException(404, "Vakansiya topilmadi")

    return {
        "id": r[0],
        "title": r[1],
        "company": r[2],
        "salary": r[3],
        "payment_type": r[4],
        "location": r[5],
        "desc": r[6],
        "user_id": r[7],
        "views_count": r[8],
        "created_at": r[9],
"applications_count": r[10],
        "experience_required": r[11],
        "employment_type": r[12],
        "work_mode": r[13],
        "work_time": r[14],

        "education_levels":[{"level": r[15]}],
        "gender": r[16],
        "job_for": r[17],

        "age_required": r[18],
        "min_age": r[19],
        "max_age": r[20],

        "field": r[21],
        "english_level": r[22],
        "russian_level": r[23],

        "lat": r[24],
        "lng": r[25]
    }
# ==========================
# 🔹 VAKANSIYA QO‘SHISH
# ==========================
@app.post("/jobs")
def create_job(data = Body(...)):

    conn = get_db()
    cur = conn.cursor()
    district = data.get("district")
    min_age = data.get("min_age")
    max_age = data.get("max_age")

    if min_age == "":
        min_age = None

    if max_age == "":
        max_age = None

    cur.execute("""
        INSERT INTO jobs
        (
            title,
            company,
            salary,
            payment_type,
            location,
            description,
            field,
            user_id,
            experience_required,
            employment_type,
            work_mode,
            work_time,
            education_level,
            gender,
            job_for,
            lat,
            lng,
            age_required,
            min_age,
            max_age,
            english_level,
            russian_level,
            district
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["title"],
        data["company"],
        data["salary"],
        data.get("payment_type"),
        data.get("location"),
        data.get("desc",""),
        data.get("field"),
        data["user_id"],
        data.get("experience_required"),
        data.get("employment_type"),
        data.get("work_mode"),
        data.get("work_time"),
        data.get("education_levels")[0]["level"],
        data.get("gender"),
        data.get("job_for"),
        data.get("lat"),
        data.get("lng"),
        data.get("age_required"),
        min_age,
        max_age,
        data.get("english_level"),
        data.get("russian_level"),
        district
    ))

    conn.commit()
    conn.close()

    return {"message": "success"}

# ==========================
# 🔹 REGISTER
# ==========================

from fastapi import Body, HTTPException
import bcrypt


def to_int(v):
    if v in ("", None):
        return None
    return int(v)


@app.post("/register")
def register(data: dict = Body(...)):

    conn = get_db()
    cur = conn.cursor()

    try:

        # EMAIL CHECK
        cur.execute(
            "SELECT id FROM users WHERE email=%s",
            (data["email"],)
        )

        if cur.fetchone():
            raise HTTPException(400, "Bu email avval ro'yxatdan o'tgan")

        password = data["password"]

        # INTEGER SAFE CONVERT
        experience = to_int(data.get("experience"))
        salary = to_int(data.get("salary"))
        birth_year = to_int(data.get("birth_year"))

        # USER INSERT
        cur.execute("""
            INSERT INTO users(
                name,
                surname,
                phone,
                email,
                password,
                role,
                district,
                education,
                field,
                experience,
                salary,
                negotiable,
                about,
                birth_year,
                english_level,
                russian_level,
                lat,
                lng,
                address
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            data.get("name"),
            data.get("surname"),
            data.get("phone"),
            data.get("email"),
            password,
            data.get("role", "worker"),
            data.get("district"),
            data.get("education"),
            data.get("field"),
            experience,
            salary,
            data.get("negotiable"),
            data.get("about"),
            birth_year,
            data.get("english_level"),
            data.get("russian_level"),
            data.get("lat"),
            data.get("lng"),
            data.get("address")
        ))

        user_id = cur.fetchone()[0]

        # SKILLS INSERT
        skills = data.get("skills", [])

        for skill_id in skills:
            cur.execute(
                "INSERT INTO user_skills (user_id, skill_id) VALUES (%s,%s)",
                (user_id, skill_id)
            )

        conn.commit()

        return {"status": "ok"}

    finally:
        conn.close()

# ==========================
# 🔹 LOGIN
# ==========================
@app.post("/login")
def login(data: UserLogin):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, email, password, role
        FROM users
        WHERE email=%s
    """, (data.email,))

    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(400, "Foydalanuvchi topilmadi")

    if row[3] != data.password:
        raise HTTPException(400, "Parol noto‘g‘ri")

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[4]
    }


# ==========================
# 🔹 ARIZA YUBORISH
# ==========================
# ==========================
# 🔹 ARIZA YUBORISH
# ==========================

@app.post("/apply")
async def apply(data = Body(...)):

    conn = get_db()
    cur = conn.cursor()

    try:

        worker_age = data["age"]
        worker_exp = data["experience"]
        worker_edu = data["education"]
        worker_gender = data["gender"]

        worker_eng = data.get("english_level")
        worker_rus = data.get("russian_level")

        cur.execute("""
            SELECT
                age_required,
                min_age,
                max_age,
                experience_required,
                education_level,
                gender,
                english_level,
                russian_level
            FROM jobs
            WHERE id=%s
        """, (data["job_id"],))

        job = cur.fetchone()

        if not job:
            raise HTTPException(404, "Vakansiya topilmadi")

        age_required, min_age, max_age, req_exp, req_edu, req_gender, req_eng, req_rus = job

        score = 0

        # TAJRIBA (30%)

        if req_exp and worker_exp:

            try:
                needed = int(req_exp.split()[0])
                worker_exp = int(worker_exp)

                if worker_exp >= needed:
                    score += 30

            except:
                pass


        # TALIM (20%)

        edu_levels = {
            "O'rta":1,
            "Bakalavr":2,
            "Magistr":3
        }

        if req_edu == "Ahamiyatsiz":
            score += 20

        elif worker_edu in edu_levels and req_edu in edu_levels:

            if edu_levels[worker_edu] >= edu_levels[req_edu]:
                score += 20


        # JINS (10%)

        if req_gender == "Ahamiyatsiz":
            score += 10

        elif worker_gender == req_gender:
            score += 10


        # YOSH (10%)

        if age_required == "Ahamiyatsiz":
            score += 10

        else:

            if min_age and worker_age < min_age:
                raise HTTPException(
                    400,
                    f"Sizning yoshingiz ({worker_age}) bu ish uchun juda kichik"
                )

            if max_age and worker_age > max_age:
                raise HTTPException(
                    400,
                    f"Sizning yoshingiz ({worker_age}) bu ish uchun katta"
                )

            score += 10


        # ENGLISH IELTS (10%)

        if req_eng and req_eng != "none":

            try:

                if float(worker_eng) >= float(req_eng):
                    score += 10

            except:
                pass


        # RUSSIAN (10%)

        levels = {
            "A1":1,
            "A2":2,
            "B1":3,
            "B2":4,
            "C1":5
        }

        if req_rus and req_rus != "none":

            if worker_rus in levels and req_rus in levels:

                if levels[worker_rus] >= levels[req_rus]:
                    score += 10


        match_percent = score


        cur.execute("""
            SELECT id FROM applications
            WHERE job_id=%s AND user_id=%s
        """, (data["job_id"], data["user_id"]))

        if cur.fetchone():
            raise HTTPException(400, "Siz bu ishga allaqachon ariza yuborgansiz")


        cur.execute("""
            INSERT INTO applications
            (
                job_id,
                user_id,
                message,
                status,
                match_percent,
                worker_age,
                worker_experience,
                worker_education,
                worker_gender
            )
            VALUES (%s,%s,%s,'waiting',%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            data["job_id"],
            data["user_id"],
            data["message"],
            match_percent,
            worker_age,
            worker_exp,
            worker_edu,
            worker_gender
        ))

        app_id = cur.fetchone()[0]
        conn.commit()

    except HTTPException:
        conn.rollback()
        conn.close()
        raise

    except Exception:
        conn.rollback()
        conn.close()
        raise HTTPException(500, "Server xatosi")

    conn.close()

    # 🔔 EMPLOYER NOTIFICATION
    conn2 = get_db()
    cur2 = conn2.cursor()

    cur2.execute(
    "SELECT user_id FROM jobs WHERE id=%s",
    (data["job_id"],)
)

    owner = cur2.fetchone()
    conn2.close()

    if owner:

        owner_id = owner[0]

        if owner_id in active_connections:
             for connection in active_connections[owner_id]:
                 await connection.send_json({
                     "type": "new_application",
                     "application_id": app_id
                 })

    return {
    "message": "ok",
    "application_id": app_id,
    "match": match_percent
}
# ==========================
# 🔹 WORKER O‘Z ARIZALARI
# ==========================
@app.get("/myapplications/{user_id}")
def get_my_applications(user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            a.id,
            a.job_id,
            j.title,
            j.company,
            a.status,
            a.message
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.user_id = %s
        ORDER BY a.id DESC
    """, (user_id,))

    rows = cur.fetchall()

    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "job_id": r[1],
            "title": r[2],
            "company": r[3],
            "status": r[4],
            "message": r[5]
        })

    conn.close()
    return result


# ==========================
# 🔹 EMPLOYER — KELGAN ARIZALAR
# ==========================
@app.get("/applications/{job_id}/{owner_id}")
def get_applications(job_id: int, owner_id: int):

    conn = get_db()
    cur = conn.cursor()

    # JOB OWNER TEKSHIRISH
    cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
    job = cur.fetchone()

    if not job or job[0] != owner_id:
        raise HTTPException(403, "Siz bu vakansiya arizalarini ko‘ra olmaysiz")

    # APPLICATIONLARNI OLISH
    cur.execute("""
        SELECT 
            a.id,
            a.user_id,
            u.name,
            u.email,
            a.message,
            a.status,
            a.match_percent
        FROM applications a
        JOIN users u ON u.id = a.user_id
        WHERE a.job_id = %s
        ORDER BY a.match_percent DESC
    """, (job_id,))

    rows = cur.fetchall()
    conn.close()

    result = []

    for r in rows:
        result.append({
            "id": r[0],
            "worker_id": r[1],
            "name": r[2],
            "email": r[3],
            "message": r[4],
            "status": r[5],
            "percent": r[6]
        })

    return result
# ==========================
# 🔹 ACCEPT
# ==========================
@app.put("/applications/{app_id}/accept/{user_id}")
async def accept_app(app_id: int, user_id: int):

    conn = get_db()
    cur = conn.cursor()

    # 🔎 tekshir
    cur.execute("""
        SELECT j.user_id, a.user_id
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        WHERE a.id=%s
    """, (app_id,))

    row = cur.fetchone()

    if not row:
        conn.close()
        raise HTTPException(404, "Ariza topilmadi")

    employer_id, worker_id = row

    if employer_id != user_id:
        conn.close()
        raise HTTPException(403, "Ruxsat yo‘q")

    # ✅ update
    cur.execute("""
        UPDATE applications
        SET status='accepted'
        WHERE id=%s
    """, (app_id,))

    conn.commit()
    conn.close()

    # 🔥 workerga real-time signal
    if worker_id in active_connections:
        for connection in active_connections[worker_id]:
            await connection.send_json({
                "type": "application_accepted",
                "application_id": app_id
            })

    return {"message": "accepted"}


# ==========================
# 🔹 REJECT
# ==========================
@app.put("/applications/{app_id}/reject/{user_id}")
def reject_app(app_id: int, user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT j.user_id
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        WHERE a.id=%s
    """, (app_id,))

    row = cur.fetchone()

    if not row:
        conn.close()
        raise HTTPException(404, "Ariza topilmadi")

    if row[0] != user_id:
        conn.close()
        raise HTTPException(403, "Bu ariza sizning vakansiyangizga tegishli emas!")

    cur.execute("""
        UPDATE applications
        SET status='rejected'
        WHERE id=%s
    """, (app_id,))

    conn.commit()
    conn.close()

    return {"message": "rejected"}

# ==========================
# 🔹 FAQAT O‘Z VAKANSIYALARI
# ==========================
@app.get("/myjobs/{user_id}")
def my_jobs(user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            j.id,
            j.title,
            j.company,
            j.salary,
            j.location,
            j.description,
            j.created_at,
            j.views_count,
            j.status,

            COUNT(a.id) AS applications_count

        FROM jobs j

        LEFT JOIN applications a
        ON j.id = a.job_id

        WHERE j.user_id = %s

        GROUP BY j.id
        ORDER BY j.created_at DESC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    result = []

    for r in rows:
        result.append({
            "id": r[0],
            "title": r[1],
            "company": r[2],
            "salary": r[3],
            "location": r[4],
            "description": r[5],
            "created_at": r[6],
            "views_count": r[7],
            "status": r[8],
            "applications_count": r[9]
        })

    return result

# ==========================
# 🔹 delete
# ==========================
@app.delete("/jobs/{job_id}/{user_id}")
def delete_job(job_id: int, user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(404, "Vakansiya topilmadi")

    if row[0] != user_id:
        raise HTTPException(403, "Bu vakansiya sizga tegishli emas!")

    cur.execute("DELETE FROM jobs WHERE id=%s", (job_id,))
    conn.commit()
    conn.close()

    return {"message": "deleted"}

# ================================
# EMPLOYER UCHUN YANGI ARIZALAR SONI
# ================================

@app.get("/notifications/{user_id}")
def notifications(user_id: int):

    conn = get_db()
    cur = conn.cursor()

    # 🔔 jami arizalar soni
    cur.execute("""
        SELECT COUNT(*)
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        WHERE j.user_id=%s AND a.status='waiting'
    """, (user_id,))
    
    applications = cur.fetchone()[0]


    # 🔔 qaysi jobga nechta ariza kelgan
    cur.execute("""
        SELECT j.id, j.title, COUNT(a.id)
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        WHERE j.user_id=%s AND a.status='waiting'
        GROUP BY j.id, j.title
    """, (user_id,))

    rows = cur.fetchall()

    by_jobs = []

    for r in rows:
        by_jobs.append({
            "job_id": r[0],
            "title": r[1],
            "count": r[2]
        })


    # 💬 unread messages
    cur.execute("""
        SELECT COUNT(*)
        FROM messages m
        JOIN jobs j ON j.id = m.job_id
        WHERE j.user_id=%s
        AND m.sender_id != %s
        AND m.seen = false
    """, (user_id, user_id))

    messages = cur.fetchone()[0]

    conn.close()

    return {
        "total": applications + messages,
        "applications": applications,
        "messages": messages,
        "by_jobs": by_jobs
    }
@app.get("/debug/apps")
def debug():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, job_id, status, user_id FROM applications")
    apps = cur.fetchall()

    cur.execute("SELECT id, title, user_id FROM jobs")
    jobs = cur.fetchall()

    conn.close()

    return {
        "applications": apps,
        "jobs": jobs
    }

# ================================
# APPLICATIONLARNI KO‘RILGAN DEB BELGILASH
# ================================
@app.put("/applications/seen/{job_id}/{user_id}")
def applications_seen(job_id: int, user_id: int):

    conn = get_db()
    cur = conn.cursor()

    # faqat shu employer jobi bo‘lsa
    cur.execute("""
        UPDATE applications a
        SET status='seen'
        FROM jobs j
        WHERE a.job_id=j.id
          AND a.job_id=%s
          AND j.user_id=%s
          AND a.status='waiting'
    """, (job_id, user_id))

    conn.commit()
    conn.close()

    return {"message": "seen updated"}



# ===============================
# WEBSOCKET MANAGER
# ===============================


active_connections: Dict[int, List[WebSocket]] = {}
chat_connections: Dict[str, List[WebSocket]] = {}


# ===============================
# 🔔 NOTIFICATION SOCKET
# ===============================

@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: int):

    await websocket.accept()

    if user_id not in active_connections:
        active_connections[user_id] = []

    active_connections[user_id].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        if user_id in active_connections:
            if websocket in active_connections[user_id]:
                active_connections[user_id].remove(websocket)


# ===============================
# 💬 CHAT SOCKET
# ===============================

@app.websocket("/ws/chat/{job_id}/{worker_id}/{sender_id}")
async def websocket_chat(websocket: WebSocket, job_id: int, worker_id: int, sender_id: int):

    room = f"{job_id}_{worker_id}"

    print("TRY CONNECT:", room, sender_id)

    await websocket.accept()

    print("CONNECTED:", room, sender_id)

    if room not in chat_connections:
        chat_connections[room] = []

    chat_connections[room].append(websocket)

    try:
        while True:

            data = await websocket.receive_json()
            text = data.get("text")

            print("MESSAGE:", text)

            # 🔥 DATABASE GA SAQLASH
            conn = get_db()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO messages (job_id, worker_id, sender_id, text, seen)
                VALUES (%s,%s,%s,%s,false)
            """, (job_id, worker_id, sender_id, text))

            conn.commit()
            conn.close()

            # 🔔 employer notification
            conn2 = get_db()
            cur2 = conn2.cursor()

            cur2.execute(
                "SELECT user_id FROM jobs WHERE id=%s",
                (job_id,)
            )

            owner = cur2.fetchone()
            conn2.close()

            if owner:

                employer_id = owner[0]

                if employer_id in active_connections:
                    for connection in active_connections[employer_id]:
                        await connection.send_json({
                            "type": "new_message"
                        })

            # 🔥 FAQAT SHU ROOM DAGILARGA YUBORISH
            for connection in chat_connections[room]:
                await connection.send_json({
                    "sender_id": sender_id,
                    "text": text,
                    "time": datetime.now().strftime("%H:%M")
                })

    except Exception as e:
        print("WEBSOCKET ERROR:", e)

    finally:
        if room in chat_connections:
            if websocket in chat_connections[room]:
                chat_connections[room].remove(websocket)

        print("DISCONNECTED:", room)
# ===============================
# 📜 OLD MESSAGES
# ===============================
@app.get("/messages/{job_id}/{worker_id}")
def get_messages(job_id: int, worker_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT sender_id, text, created_at
        FROM messages
        WHERE job_id=%s AND worker_id=%s
        ORDER BY created_at
    """, (job_id, worker_id))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "sender_id": r[0],
            "text": r[1],
            "time": r[2].strftime("%H:%M")
        }
        for r in rows
    ]

@app.put("/messages/seen/{job_id}/{worker_id}")
def mark_seen(job_id: int, worker_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE messages
        SET seen = true
        WHERE job_id=%s AND worker_id=%s
    """, (job_id, worker_id))

    conn.commit()
    conn.close()

    return {"message": "seen"}


@app.get("/skills")
def get_skills(field: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name
        FROM skills
        WHERE field=%s
        ORDER BY name
    """, (field,))

    skills = cur.fetchall()

    conn.close()

    return [
        {"id": s[0], "name": s[1]}
        for s in skills
    ]

@app.get("/users/{user_id}/skills")
def get_user_skills(user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.id, s.name
        FROM skills s
        JOIN user_skills us
        ON s.id = us.skill_id
        WHERE us.user_id = %s
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {"id": r[0], "name": r[1]}
        for r in rows
    ]

@app.get("/chat/workers/{job_id}")
def chat_workers(job_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT u.id, u.name
        FROM applications a
        JOIN users u ON u.id = a.user_id
        WHERE a.job_id=%s AND a.status='accepted'
        ORDER BY u.name
    """, (job_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "worker_id": r[0],
            "name": r[1]
        }
        for r in rows
    ]

@app.get("/chat/check/{job_id}/{user_id}")
def check_chat(job_id: int, user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT status
        FROM applications
        WHERE job_id=%s AND user_id=%s
    """, (job_id, user_id))

    row = cur.fetchone()
    conn.close()

    if not row or row[0] != "accepted":
        raise HTTPException(403, "Chat ruxsati yo'q")

    return {"chat": True}


@app.get("/employer/jobs/{user_id}")
def employer_jobs(user_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title
        FROM jobs
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "title": r[1]
        }
        for r in rows
    ]

# ==========================
# 🔹 VAKANSIYA TAHRIRLASH
# ==========================

@app.put("/jobs/{job_id}")
def update_job(job_id: int, data = Body(...)):

    conn = get_db()
    cur = conn.cursor()

    # 🔐 owner tekshirish
    cur.execute("SELECT user_id FROM jobs WHERE id=%s", (job_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        raise HTTPException(404, "Vakansiya topilmadi")

    if row[0] != data.get("user_id"):
        conn.close()
        raise HTTPException(403, "Bu vakansiya sizga tegishli emas")

    min_age = data.get("min_age")
    max_age = data.get("max_age")

    if min_age == "":
        min_age = None
    if max_age == "":
        max_age = None

    cur.execute("""
        UPDATE jobs
        SET
            title=%s,
            company=%s,
            salary=%s,
            payment_type=%s,
            location=%s,
            description=%s,
            field=%s,
            experience_required=%s,
            employment_type=%s,
            work_mode=%s,
            work_time=%s,
            education_level=%s,
            gender=%s,
            job_for=%s,
            lat=%s,
            lng=%s,
            age_required=%s,
            min_age=%s,
            max_age=%s,
            english_level=%s,
            russian_level=%s
        WHERE id=%s
    """, (
        data.get("title"),
        data.get("company"),
        data.get("salary"),
        data.get("payment_type"),
        data.get("location"),
        data.get("desc"),
        data.get("field"),
        data.get("experience_required"),
        data.get("employment_type"),
        data.get("work_mode"),
        data.get("work_time"),
        data.get("education_levels")[0]["level"],
        data.get("gender"),
        data.get("job_for"),
        data.get("lat"),
        data.get("lng"),
        data.get("age_required"),
        min_age,
        max_age,
        data.get("english_level"),
        data.get("russian_level"),
        job_id
    ))

    conn.commit()
    conn.close()

    return {"message": "updated"}



@app.get("/workers")
def get_workers():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            u.id,
            u.name,
            u.surname,
            u.field,
            u.experience,
            u.salary,
            u.district,
            education, 
            u.lat,
            u.lng,
            COALESCE(array_agg(s.name) FILTER (WHERE s.name IS NOT NULL), '{}') AS skills
        FROM users u
        LEFT JOIN user_skills us ON u.id = us.user_id
        LEFT JOIN skills s ON us.skill_id = s.id
        WHERE u.role = 'worker'
        GROUP BY u.id
        ORDER BY u.id DESC
    """)

    rows = cur.fetchall()

    result = []

    for r in rows:
        result.append({
            "id": r[0],
            "name": r[1],
            "surname": r[2],
            "field": r[3],
            "experience": r[4],
            "salary": r[5],
            "district": r[6],
            "education": r[7],
            "lat": float(r[8]) if r[8] else None,
            "lng": float(r[9]) if r[9] else None,
            "skills": r[10]  # 👈 skilllar shu yerda
        })

    conn.close()

    return result

@app.get("/workers/{worker_id}")
def get_worker(worker_id: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            u.id,
            u.name,
            u.surname,
            u.field,
            u.experience,
            u.salary,
            u.district,
            u.education,
            u.birth_year,
            u.english_level,
            u.russian_level,
            u.phone,
            u.lat,
            u.lng,
            u.address,
            u.about,
            COALESCE(array_agg(s.name) FILTER (WHERE s.name IS NOT NULL), '{}') AS skills
        FROM users u
        LEFT JOIN user_skills us ON u.id = us.user_id
        LEFT JOIN skills s ON us.skill_id = s.id
        WHERE u.id = %s
        GROUP BY u.id
    """,(worker_id,))

    r = cur.fetchone()

    result = {
        "id": r[0],
        "name": r[1],
        "surname": r[2],
        "field": r[3],
        "experience": r[4],
        "salary": r[5],
        "district": r[6],
        "education": r[7],
        "birth_year": r[8],
        "english_level": r[9],
        "russian_level": r[10],
        "phone": r[11],
        "lat": float(r[12]) if r[12] else None,
        "lng": float(r[13]) if r[13] else None,
        "address": r[14],
        "about": r[15],
        "skills": r[16]
    }

    conn.close()

    return result

@app.get("/platform-stats")
def platform_stats():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM jobs")
    jobs = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE role='worker'")
    workers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE role='employer'")
    companies = cur.fetchone()[0]

    conn.close()

    return {
        "jobs": jobs,
        "workers": workers,
        "companies": companies
    }
