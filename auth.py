# auth.py
from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Session, create_engine, select

# ───────── Config ─────────
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"
ACCESS_TOKEN_MIN = int(os.getenv("ACCESS_TOKEN_MIN", "120"))
DB_URL = os.getenv("DB_URL", "sqlite:///./vocius.db")
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() == "true"

_engine_kwargs = {"connect_args": {"check_same_thread": False}} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, echo=False, **_engine_kwargs)
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str | None = Field(default=None, unique=True, index=True)
    email: str | None = Field(default=None, unique=True, index=True)
    name: str | None = None
    provider: str = "local"              # "local" | "google" | "github"
    password_hash: str | None = None     # local only
    role: str = "user"                   # "user" | "admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime | None = None

def init_db():
    SQLModel.metadata.create_all(engine)

init_db()

def _hash(pw: str) -> str:
    return pwd.hash(pw)

def _verify(pw: str, h: str | None) -> bool:
    return bool(h) and pwd.verify(pw, h)

def _make_token(user: User) -> str:
    payload = {
        "uid": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_MIN),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def _get_user_by_identifier(session: Session, ident: str) -> Optional[User]:
    stmt = select(User).where((User.username == ident) | (User.email == ident))
    return session.exec(stmt).first()

def require_user(authorization: str = Header(None)) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    payload = _decode(token)
    with Session(engine) as s:
        user = s.get(User, payload.get("uid"))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

def require_user_optional(authorization: str = Header(None)) -> Optional[User]:
    if not authorization:
        return None
    try:
        return require_user(authorization)
    except HTTPException:
        return None

def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user

router = APIRouter(prefix="/auth", tags=["auth"])

# ───────── Local (optional) ─────────
@router.post("/register")
def register(payload: dict):
    username = (payload.get("username") or "").strip()
    email    = (payload.get("email") or "").strip().lower()
    name     = (payload.get("name") or "").strip() or None
    password = payload.get("password") or ""
    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="username, email, password required")

    with Session(engine) as s:
        if s.exec(select(User).where(User.username == username)).first():
            raise HTTPException(status_code=409, detail="Username already taken")
        if s.exec(select(User).where(User.email == email)).first():
            raise HTTPException(status_code=409, detail="Email already registered")

        is_first = s.exec(select(User)).first() is None
        user = User(
            username=username,
            email=email,
            name=name,
            provider="local",
            password_hash=_hash(password),
            role="admin" if is_first else "user",
        )
        s.add(user); s.commit(); s.refresh(user)
        token = _make_token(user)
        return {"ok": True, "token": token, "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "name": user.name, "role": user.role,
            "created_at": user.created_at.isoformat() + "Z",
        }}

@router.post("/login")
def login(payload: dict):
    ident = (payload.get("identifier") or "").strip()
    password = payload.get("password") or ""
    if not ident or not password:
        raise HTTPException(status_code=400, detail="identifier and password required")

    with Session(engine) as s:
        user = _get_user_by_identifier(s, ident)
        if not user or not _verify(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user.last_login = datetime.utcnow()
        s.add(user); s.commit()
        token = _make_token(user)
        return {"ok": True, "token": token, "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "name": user.name, "role": user.role,
            "created_at": user.created_at.isoformat() + "Z",
        }}

@router.get("/me")
def me(user: User = Depends(require_user)):
    return {"ok": True, "user": {
        "id": user.id, "username": user.username, "email": user.email,
        "name": user.name, "role": user.role,
        "created_at": user.created_at.isoformat() + "Z",
        "last_login": user.last_login.isoformat() + "Z" if user.last_login else None,
    }}

@router.get("/admin/users")
def list_users(_: User = Depends(require_admin)):
    with Session(engine) as s:
        rows = s.exec(select(User).order_by(User.created_at.desc())).all()
        return {"ok": True, "users": [{
            "id": u.id, "username": u.username, "email": u.email, "name": u.name,
            "role": u.role, "created_at": u.created_at.isoformat() + "Z",
            "last_login": u.last_login.isoformat() + "Z" if u.last_login else None,
            "provider": u.provider,
        } for u in rows]}

# ───────── OAuth (Google & GitHub via authlib) ─────────
from authlib.integrations.starlette_client import OAuth, OAuthError

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL  = os.getenv("BACKEND_URL",  "http://127.0.0.1:3033")
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID     = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")

oauth = OAuth()
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
    oauth.register(
        name="github",
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET,
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "read:user user:email"},
    )

@router.get("/google/login")
async def google_login(request: Request):
    if "google" not in oauth._clients:
        raise HTTPException(503, "Google OAuth not configured")
    redirect_uri = f"{BACKEND_URL}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request):
    if "google" not in oauth._clients:
        raise HTTPException(503, "Google OAuth not configured")
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(400, f"Google auth error: {getattr(e, 'error', str(e))}")
    userinfo = token.get("userinfo") or await oauth.google.parse_id_token(request, token)
    email = (userinfo or {}).get("email")
    if not email:
        raise HTTPException(400, "Google did not return email")
    name = (userinfo.get("name") or userinfo.get("given_name") or "").strip()
    username_guess = email.split("@")[0]

    with Session(engine) as s:
        user = s.exec(select(User).where(User.email == email)).first()
        if not user:
            user = User(username=username_guess, email=email, name=name or None, provider="google", role="user")
            s.add(user); s.commit(); s.refresh(user)
        user.last_login = datetime.utcnow()
        s.add(user); s.commit()

    jwt_token = _make_token(user)
    return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}")

@router.get("/github/login")
async def github_login(request: Request):
    if "github" not in oauth._clients:
        raise HTTPException(503, "GitHub OAuth not configured")
    redirect_uri = f"{BACKEND_URL}/auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)

@router.get("/github/callback")
async def github_callback(request: Request):
    if "github" not in oauth._clients:
        raise HTTPException(503, "GitHub OAuth not configured")
    try:
        token = await oauth.github.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(400, f"GitHub auth error: {getattr(e, 'error', str(e))}")

    r_user = await oauth.github.get("user", token=token)
    user_data = r_user.json()

    email = user_data.get("email")
    if not email:
        r_emails = await oauth.github.get("user/emails", token=token)
        emails = r_emails.json()
        primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
        email = (primary or (emails[0] if emails else {})).get("email") if emails else None
    if not email:
        raise HTTPException(400, "GitHub email not available (grant email scope or make it public).")

    username = user_data.get("login") or email.split("@")[0]
    name = user_data.get("name") or username

    with Session(engine) as s:
        user = s.exec(select(User).where(User.email == email)).first()
        if not user:
            user = User(username=username, email=email, name=name, provider="github", role="user")
            s.add(user); s.commit(); s.refresh(user)
        user.last_login = datetime.utcnow()
        s.add(user); s.commit()

    jwt_token = _make_token(user)
    return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}")

# ───────── NextAuth upsert hook ─────────
@router.post("/oauth/upsert")
def oauth_upsert(payload: dict):
    """
    Called by NextAuth `events.signIn`. Creates or updates the user and stamps last_login.
    Body: { email, name?, provider? }
    """
    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="email required")

    name = (payload.get("name") or "").strip() or None
    provider = (payload.get("provider") or "google").strip()

    with Session(engine) as s:
        user = s.exec(select(User).where(User.email == email)).first()
        if user:
            user.name = user.name or name
            user.provider = provider or user.provider
            user.last_login = datetime.utcnow()
            s.add(user); s.commit(); s.refresh(user)
        else:
            username = email.split("@")[0]
            user = User(
                username=username,
                email=email,
                name=name,
                provider=provider,
                role="user",
                last_login=datetime.utcnow(),
            )
            s.add(user); s.commit(); s.refresh(user)

    return {
        "ok": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "provider": user.provider,
            "created_at": user.created_at.isoformat() + "Z",
            "last_login": user.last_login.isoformat() + "Z" if user.last_login else None,
        },
    }
