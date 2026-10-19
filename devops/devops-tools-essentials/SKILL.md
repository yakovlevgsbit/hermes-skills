---
name: devops-tools-essentials
description: "Use when setting up DevOps infrastructure."
---

# DevOps Tools Essentials

> **Полный разбор**: `/root/kb/projects/devops-tools-essentials.md`

## Top Repositories

| Репозиторий | Stars | Тема |
|-------------|-------|------|
| ArgoCD | 24.4k | GitOps CD для Kubernetes |
| SOPS | 23.3k | Secrets management (YAML/JSON/ENV) |
| Kestra | 29.8k | Self-hosted Git + CI/CD |
| Gitea | 45.6k | Self-hosted Git service |
| Sentry | 45.6k | Error tracking |

## Key Patterns

1. **GitOps** — Git как единственный источник истины (ArgoCD, FluxCD)
2. **Secrets encryption** — SOPS: зашифрованные файлы в Git, multi-backend (KMS + age)
3. **Self-hosted first** — почти всё можно запустить локально через Docker
4. **Declarative sync** — pull-based, не push (сам кластер тянет изменения)
5. **Multi-cluster management** — ArgoCD для управления многими кластерами

## ArgoCD Quick Start

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-c/stable/manifests/install.yaml
```

## SOPS Quick Start

```bash
sops -i --age age1... secrets.yaml  # encrypt
sops -d secrets.yaml               # decrypt
sops secrets.yaml                  # edit
```

## Итог

DevOps tools — GitOps, secrets, self-hosted Git, error tracking. Ключевая идея: Git как источник истины, self-hosted для контроля.