# Secrets Management

Configuration and secrets patterns from solo development to team production. Back to [SKILL.md](../SKILL.md).

## Progression

```
Solo dev          Team dev           Team production      Enterprise
.env files   -->  SOPS + age    -->  SOPS + age      -->  1Password CLI
(gitignored)      (encrypted,        (encrypted,           or Vault
                   git-tracked)       git-tracked)
```

**Default recommendation: SOPS + age** for any team project. Free, git-friendly, no cloud services required.

## Level 1: .env Files (Solo Dev)

The simplest approach. Never committed to git.

### Pattern

```bash
# .env (gitignored -- never committed)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app
REDIS_URL=redis://localhost:6379
SECRET_KEY=dev-secret-change-in-prod
OLLAMA_URL=http://localhost:11434

# .env.example (committed -- documents required variables)
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379
SECRET_KEY=
OLLAMA_URL=http://localhost:11434
```

### Docker Compose Integration

```yaml
services:
  app:
    env_file: [.env]
    environment:
      NODE_ENV: development  # Overrides .env values
```

### Gotchas

- **`.env` MUST be in `.gitignore`** -- this is the #1 secret leak vector
- **No encryption** -- anyone with file access sees all secrets
- **No audit trail** -- no way to know when a secret was changed or by whom
- **Manual sharing** -- team members copy `.env` files via Slack, email (insecure)

## Level 1.5: direnv (Auto-Loading)

Shell extension that automatically loads `.env` files when you enter a directory.

```bash
# Install
brew install direnv  # macOS
# Add to shell: eval "$(direnv hook zsh)"

# Create .envrc
echo 'dotenv' > .envrc
direnv allow  # Required after any change (security feature)
```

**Benefit:** Environment variables are loaded automatically -- no need to `source .env` or prefix commands with `dotenv`. Works with any tool, not just Docker Compose.

## Level 2: SOPS + age (Team Projects)

**SOPS** (Secrets OPerationS) encrypts only the *values* in YAML/JSON/ENV files, preserving keys for readability and git diffs. **age** is a modern, simple encryption tool (recommended over GPG).

### Setup

```bash
# Install
brew install sops age  # macOS

# Generate a key pair
age-keygen -o ~/.config/sops/age/keys.txt
# Outputs: public key: age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
```

### Configuration

Create `.sops.yaml` in the project root:

```yaml
creation_rules:
  - path_regex: \.env\.encrypted$
    age: >-
      age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p,
      age1abc...second_team_member_public_key
  - path_regex: secrets/.*\.yaml$
    age: >-
      age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
```

### Workflow

```bash
# Create encrypted file from plaintext
sops --encrypt .env > .env.encrypted

# Edit encrypted file (decrypts in $EDITOR, re-encrypts on save)
sops .env.encrypted

# Decrypt to stdout (for CI/CD or Docker)
sops --decrypt .env.encrypted > .env

# Encrypt a YAML file
sops --encrypt secrets/production.yaml > secrets/production.enc.yaml
```

### What Gets Committed

```
.env                    # NEVER (gitignored)
.env.example            # Always (empty values, documents structure)
.env.encrypted          # Always (encrypted values, safe to commit)
.sops.yaml              # Always (encryption configuration)
```

### Adding a Team Member

```bash
# Team member generates their key
age-keygen -o ~/.config/sops/age/keys.txt

# They share their PUBLIC key (safe to share)
# Add it to .sops.yaml creation_rules

# Re-encrypt existing files to include the new key
sops updatekeys .env.encrypted
```

### Docker Compose Integration

```bash
# Decrypt secrets, then run compose
sops --decrypt .env.encrypted > .env && docker compose up -d
```

Or use a Makefile:

```makefile
.PHONY: up
up:
	sops --decrypt .env.encrypted > .env
	docker compose up -d
	rm .env  # Clean up plaintext after compose reads it
```

## Level 3: 1Password CLI (Enterprise)

For teams already using 1Password. Secrets are referenced by URI, never stored locally.

### Pattern

```bash
# Install
brew install 1password-cli

# Config file with secret references (safe to commit)
# .env.1password
DATABASE_URL=op://Engineering/Production DB/connection_string
SECRET_KEY=op://Engineering/App Secrets/secret_key
API_TOKEN=op://Engineering/External API/token
```

### Usage

```bash
# Inject secrets as environment variables
op run --env-file=.env.1password -- docker compose up -d

# Or inject into a template file
op inject -i config.template.yaml -o config.yaml
```

### When 1Password Over SOPS

- Team already pays for 1Password ($7.99/user/month Business plan)
- Need centralized secret rotation
- Need audit trails for secret access
- Want to avoid managing encryption keys

## Comparison

| Tool | Encryption | Git-Friendly | Team Sharing | Cost | Complexity |
|------|-----------|--------------|--------------|------|------------|
| `.env` files | None | No (gitignored) | Manual copy | Free | Trivial |
| direnv | None | No | Manual | Free | Low |
| SOPS + age | At rest | Yes (encrypted values) | Public key exchange | Free | Low-Medium |
| 1Password CLI | Vault-based | Yes (references only) | Via vault sharing | $7.99/user/mo | Low |
| Docker Secrets | At rest | N/A | Via Swarm | Free | Medium |
| HashiCorp Vault | At rest + transit | No (API-based) | Policies + tokens | Free (OSS) / Paid | High |

## Secrets in Docker Compose

Docker Compose supports a `secrets` top-level element, but it has limitations:

```yaml
secrets:
  db_password:
    file: ./secrets/db_password.txt

services:
  db:
    image: postgres:17
    secrets: [db_password]
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
```

**Limitation:** file-based secrets work, but the application must read from `/run/secrets/` rather than environment variables. Not all applications support this. SOPS + age is more universally compatible.

## CI/CD Secret Injection

For deploying from CI/CD pipelines, secrets come from the CI platform:

| Platform | Secret Source | Usage |
|----------|-------------|-------|
| GitHub Actions | Repository/Organization secrets | `${{ secrets.DATABASE_URL }}` |
| GitLab CI | CI/CD variables | `$DATABASE_URL` |
| Cloud providers | Secrets Manager / Key Vault | IAM-based access, no static tokens |

See the [CI/CD skill](../../cicd/SKILL.md) for pipeline-specific patterns.
