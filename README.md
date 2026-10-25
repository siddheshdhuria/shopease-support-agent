# 🎫 ShopEase Support Agent: AWS Deployment + CI/CD

Colab wala LangGraph Agentic RAG project, ab **production-style** repo me: FastAPI + Docker + GitHub Actions → Amazon ECR → EC2.

```
Developer ──git push──▶ GitHub ──▶ GitHub Actions
                                     │
                 ┌───────────────────┼────────────────────┐
                 ▼                   ▼                    ▼
           1. CI: test        2. Build image        3. CD: deploy
           ruff + pytest      push → Amazon ECR     SSH → EC2: docker pull + run
                                                          │
                                         Users ──http──▶ EC2 :80 → container :8000
```

## 📁 Repo structure
```
app/
  config.py          settings env variables se (code me koi secret nahi)
  knowledge_base.py  10 ShopEase policies
  tools.py           @tool functions + lazy vector store
  agent.py           LangGraph graph + chat() function
  main.py            FastAPI (/health, /chat, /tickets, /docs) + Gradio UI at /
tests/               pytest, bina OpenAI call ke (LLM mock)
deploy/ec2-setup.sh  EC2 pe ek baar chalana
Dockerfile
.github/workflows/ci-cd.yml
```

---

## 🗓️ Teaching plan (4 sessions)

| Session | Topic | Students kya karenge |
|---|---|---|
| 1 | Notebook → Python app | Code ko modules me todna, FastAPI, `uvicorn` local run, `/docs` me API test |
| 2 | Docker | Dockerfile samajhna, `docker build`, `docker run`, env variables |
| 3 | AWS setup + manual deploy | IAM, ECR, EC2, security group, manual `docker pull/run` |
| 4 | CI/CD | GitHub Actions, secrets, auto-deploy, failing test se deploy rokna |

**Golden rule (students ko bolo):** *"Pehle manually deploy karo, phir automate karo. Jo kaam aap haath se nahi samajhte, use pipeline me daalna galti hai."*

---

## Session 1: Local run

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env        # apni OpenAI key daalo
export $(cat .env | xargs)  # Windows PowerShell me alag se set karo
uvicorn app.main:app --reload
```
- http://localhost:8000 → Gradio chat UI
- http://localhost:8000/docs → Swagger me `/chat` try karo
- `pytest -q` → 8 tests, bina API key ke

**Bolne ke liye:** *"Notebook experiment ke liye hota hai, production ke liye nahi. Production me code modules me hota hai, settings environment se aati hain, aur har feature ke tests hote hain."*

## Session 2: Docker

```bash
docker build -t shopease .
docker run -p 8000:8000 --env-file .env shopease
```
Dockerfile ke 4 points samjhao:
1. `requirements.txt` pehle copy hota hai, isse **layer cache** milta hai aur rebuild fast hota hai.
2. API key image me **nahi** jaati. Wo run time pe `--env-file` se aati hai.
3. Container **non-root user** se chalta hai.
4. `HEALTHCHECK` → `/health` endpoint.

**Bolne ke liye:** *"Docker ka matlab hai 'mere laptop pe chalta hai' wali problem khatam. Jo image yahan chali, wahi exact image AWS pe chalegi."*

---

## Session 3: AWS setup (ek baar, region: ap-south-1 Mumbai)

### 3.1 ECR repository (Docker images ka AWS store)
ECR → Create repository → name: `shopease-support-agent` (private)

### 3.2 IAM user for GitHub Actions
IAM → Users → Create user `github-actions-shopease`
- Permission: `AmazonEC2ContainerRegistryPowerUser`
- Security credentials → Create access key → **Access key ID + Secret** note karo

### 3.3 IAM role for EC2
IAM → Roles → Create role → AWS service: **EC2**
- Permission: `AmazonEC2ContainerRegistryReadOnly`
- Name: `ec2-shopease-ecr-pull`

### 3.4 EC2 instance
- AMI: **Amazon Linux 2023**, type: `t3.small` (1 GB wala `t3.micro` bhi chal jaata hai, par tight hai)
- Key pair: naya banao → `.pem` download
- Security group inbound:
  - SSH 22 (demo ke liye Anywhere, kyunki GitHub runners ke IP fixed nahi hote; production me self-hosted runner / SSM use karo)
  - HTTP 80 → Anywhere
- Advanced details → IAM instance profile → `ec2-shopease-ecr-pull`

### 3.5 Server setup
```bash
scp -i key.pem deploy/ec2-setup.sh ec2-user@<EC2_PUBLIC_IP>:~
ssh -i key.pem ec2-user@<EC2_PUBLIC_IP>
bash ec2-setup.sh        # Docker install + OpenAI key ~/shopease.env me save
exit                     # logout/login, taaki docker group apply ho
```

### 3.6 Manual deploy (pehle haath se!)
Laptop se:
```bash
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com
docker build -t <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/shopease-support-agent:v1 .
docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/shopease-support-agent:v1
```
EC2 pe:
```bash
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com
docker run -d --name shopease --restart unless-stopped -p 80:8000 --env-file ~/shopease.env <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/shopease-support-agent:v1
```
Browser: `http://<EC2_PUBLIC_IP>` 🎉

**Bolne ke liye:** *"Dekho, humne 6 commands chalaye. Har baar code badlega to ye 6 commands dobara chalane padenge. Insaan bhoolega, typo karega. Isi problem ka solution hai CI/CD."*

---

## Session 4: CI/CD with GitHub Actions

### 4.1 GitHub Secrets
Repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | Step 3.2 se |
| `AWS_SECRET_ACCESS_KEY` | Step 3.2 se |
| `EC2_HOST` | EC2 public IP |
| `EC2_SSH_KEY` | `.pem` file ka **pura content** |

`OPENAI_API_KEY` GitHub me **nahi** hai. Wo sirf EC2 ki `~/shopease.env` me hai. Tests ko key ki zarurat nahi kyunki LLM mock hai.

### 4.2 Pipeline (`.github/workflows/ci-cd.yml`)
```
Pull Request  →  test (ruff + pytest)                       ← CI
Push to main  →  test → build-and-push (ECR) → deploy (EC2)  ← CI + CD
```
- `needs:` → agla job tabhi chalega jab pichla pass ho
- Image tag = **git commit SHA**, isliye har deploy traceable hai aur rollback aasaan hai
- Deploy ke baad **smoke test** `/health` hit karta hai. Fail hua to pipeline red ho jaati hai.

### 4.3 Live demo flow 🎬
1. `git push` → Actions tab me 3 jobs live chalte dikhao
2. Browser me UI title me version (commit SHA) dikhega
3. **Change demo:** `app/main.py` me title ya `knowledge_base.py` me koi policy badlo → push → 2-3 min me live site update
4. **Failure demo (sabse important):** `tests/test_tools.py` me koi assert galat kar do → push → `test` job ❌ → build/deploy **skip**, aur production safe rehta hai
5. **Rollback:** EC2 pe purane SHA wali image `docker run` karo, ya `git revert` + push

**Bolne ke liye:**
> "CI ka matlab Continuous Integration: har code change pe automatically test chalte hain, taaki toota hua code main branch me na aaye. CD ka matlab Continuous Deployment: test pass hote hi code automatically server pe chala jaata hai. Agar test fail hua, deploy hoga hi nahi. Pipeline hamara security guard hai."

---

## ⚠️ Students ko limitations bhi batao (next level)
| Abhi | Production me |
|---|---|
| Tickets + chat memory in-memory, container restart pe gayab | DynamoDB / RDS, LangGraph Postgres checkpointer |
| Vector store in-memory | OpenSearch / pgvector / Azure AI Search |
| GitHub me long-lived AWS access keys | **GitHub OIDC** + IAM role (koi key store nahi) |
| OpenAI key file me | **AWS Secrets Manager / SSM Parameter Store** |
| SSH port 22 open | SSM Run Command, ya ECS Fargate (koi server manage nahi) |
| Single EC2, HTTP | ALB + Auto Scaling + HTTPS (ACM certificate) |

## 💰 Cleanup (class ke baad zaroor!)
- EC2 → Stop/Terminate instance
- ECR → purani images delete
- IAM access key → deactivate
