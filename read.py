API RESTful Assíncrona para Operações Bancárias com FastAPI
Visão Geral

Projeto de uma API RESTful assíncrona para gerenciamento de contas correntes, depósitos, saques e exibição de extrato bancário.

A aplicação utiliza:

FastAPI
JWT para autenticação
SQLite/PostgreSQL
SQLAlchemy Async
Pydantic
Alembic
OpenAPI/Swagger
Arquitetura modular

Porque humanos decidiram que até dinheiro virtual precisa de 14 camadas de abstração antes de mover R$10. Ainda assim, ficou sólido.

Funcionalidades
Autenticação
Registro de usuário
Login com JWT
Proteção de rotas autenticadas
Conta Corrente
Criação de conta
Consulta de saldo
Consulta de extrato
Operações Bancárias
Depósito
Saque
Histórico de transações
Segurança
Senhas criptografadas
JWT Bearer Token
Validação de saldo
Validação de valores negativos
Estrutura do Projeto
bank_api/
│
├── src/
│   ├── main.py
│   ├── database.py
│   ├── config.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── account.py
│   │   └── transaction.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── account.py
│   │   └── transaction.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── accounts.py
│   │   └── transactions.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   └── transaction_service.py
│   │
│   ├── security/
│   │   ├── hashing.py
│   │   └── jwt_handler.py
│   │
│   └── dependencies/
│       └── auth.py
│
├── requirements.txt
├── alembic.ini
└── README.md
Instalação
Criar ambiente virtual
python -m venv .venv
Ativar ambiente
Windows
.venv\Scripts\activate
Linux/Mac
source .venv/bin/activate
Instalar dependências
pip install fastapi uvicorn sqlalchemy aiosqlite asyncpg python-jose passlib[bcrypt] python-multipart alembic
Configuração do Banco
database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base


DATABASE_URL = "sqlite+aiosqlite:///./bank.db"


engine = create_async_engine(
    DATABASE_URL,
    echo=True
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)


Base = declarative_base()
Modelos
User Model
from sqlalchemy import Column, Integer, String
from src.database import Base


class User(Base):
    __tablename__ = "users"


    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
Account Model
from sqlalchemy import Column, Integer, Float, ForeignKey
from src.database import Base


class Account(Base):
    __tablename__ = "accounts"


    id = Column(Integer, primary_key=True)
    balance = Column(Float, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
Transaction Model
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from datetime import datetime
from src.database import Base


class Transaction(Base):
    __tablename__ = "transactions"


    id = Column(Integer, primary_key=True)
    type = Column(String)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


    account_id = Column(Integer, ForeignKey("accounts.id"))
Schemas
auth.py
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class LoginSchema(BaseModel):
    username: str
    password: str
transaction.py
from pydantic import BaseModel, Field


class TransactionSchema(BaseModel):
    amount: float = Field(gt=0)
Segurança JWT
jwt_handler.py
from jose import jwt
from datetime import datetime, timedelta


SECRET_KEY = "SUPER_SECRET_KEY"
ALGORITHM = "HS256"




def create_access_token(data: dict):
    payload = data.copy()


    payload["exp"] = datetime.utcnow() + timedelta(hours=2)


    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
Hash de Senha
hashing.py
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"])




def hash_password(password: str):
    return pwd_context.hash(password)




def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)
Dependência de Autenticação
auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError


security = HTTPBearer()


SECRET_KEY = "SUPER_SECRET_KEY"
ALGORITHM = "HS256"




def authenticate_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials


    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload


    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )
Rotas de Autenticação
auth.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import select


from src.schemas.auth import UserCreate, LoginSchema
from src.models.user import User
from src.database import AsyncSessionLocal
from src.security.hashing import hash_password, verify_password
from src.security.jwt_handler import create_access_token


router = APIRouter(prefix="/auth", tags=["Auth"])




@router.post("/register")
async def register(data: UserCreate):
    async with AsyncSessionLocal() as session:


        query = select(User).where(User.username == data.username)
        result = await session.execute(query)


        user = result.scalar_one_or_none()


        if user:
            raise HTTPException(400, "Usuário já existe")


        new_user = User(
            username=data.username,
            password=hash_password(data.password)
        )


        session.add(new_user)
        await session.commit()


        return {
            "message": "Usuário criado"
        }




@router.post("/login")
async def login(data: LoginSchema):
    async with AsyncSessionLocal() as session:


        query = select(User).where(User.username == data.username)
        result = await session.execute(query)


        user = result.scalar_one_or_none()


        if not user:
            raise HTTPException(401, "Credenciais inválidas")


        if not verify_password(data.password, user.password):
            raise HTTPException(401, "Credenciais inválidas")


        token = create_access_token({
            "sub": user.username
        })


        return {
            "access_token": token
        }
Rotas Bancárias
transactions.py
from fastapi import APIRouter, Depends, HTTPException
        transaction = Transaction(
            type="deposit",
            amount=data.amount,
            account_id=account.id
        )


        session.add(transaction)


        await session.commit()


        return {
            "message": "Depósito realizado",
            "balance": account.balance
        }




@router.post("/withdraw")
async def withdraw(
    data: TransactionSchema,
    user=Depends(authenticate_user)
):
    async with AsyncSessionLocal() as session:


        query = select(Account).where(Account.user_id == 1)


        result = await session.execute(query)


        account = result.scalar_one_or_none()


        if not account:
            raise HTTPException(404, "Conta não encontrada")


        if account.balance < data.amount:
            raise HTTPException(400, "Saldo insuficiente")


        account.balance -= data.amount


        transaction = Transaction(
            type="withdraw",
            amount=data.amount,
            account_id=account.id
        )


        session.add(transaction)


        await session.commit()


        return {
            "message": "Saque realizado",
            "balance": account.balance
        }
Extrato Bancário
@router.get("/statement")
async def statement(user=Depends(authenticate_user)):


    async with AsyncSessionLocal() as session:


        query = select(Transaction)


        result = await session.execute(query)


        transactions = result.scalars().all()


        return transactions
Arquivo Principal
main.py
from fastapi import FastAPI


from src.routes.auth import router as auth_router
from src.routes.transactions import router as transaction_router


app = FastAPI(
    title="Bank API",
    version="1.0.0"
)


app.include_router(auth_router)
app.include_router(transaction_router)
Executar Aplicação
uvicorn src.main:app --reload
Documentação OpenAPI

FastAPI gera automaticamente:

Swagger UI
http://localhost:8000/docs
ReDoc
http://localhost:8000/redoc

Melhorias Futuras
Produção
PostgreSQL
Docker
Redis
Rate Limiting
Refresh Tokens
Logs estruturados
Testes automatizados
CI/CD
Observabilidade
Segurança
RBAC
MFA
Blacklist JWT
Criptografia avançada
Exemplo de Fluxo
1. Registrar usuário
POST /auth/register
2. Login
POST /auth/login

Resposta:

{
  "access_token": "TOKEN"
}
3. Enviar token
Authorization: Bearer TOKEN
4. Fazer depósito
POST /transactions/deposit
5. Fazer saque
POST /transactions/withdraw
6. Consultar extrato