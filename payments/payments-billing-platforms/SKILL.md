---
name: payments-billing-platforms
description: "Use when building payment or billing integrations."
---

# Payments & Billing Platforms

> **Полный разбор**: `/root/kb/projects/payments-billing-platforms.md`

## Top Repositories

| Репозиторий | Stars | Тема |
|-------------|-------|------|
| Hyperswitch | 45.3k | Composable payments platform (Rust) |
| Polar | 10.3k | Billing для AI стартапов |
| Lago | 10.7k | Usage-based billing API |
| Stripe Samples | — | Официальные примеры Stripe |

## Key Patterns

1. **Composable** — собери свой payments stack из блоков (Hyperswitch)
2. **Intelligent routing** — автоматический выбор лучшего провайдера по цене/успешности
3. **Usage-based billing** — плати за реальное использование (Lago, Polar)
4. **AI-first billing** — заряд за токены, агентов, compute (Polar)
5. **Multi-provider** — не залочен на один payment gateway
6. **PCI compliant** — из коробки (Hyperswitch)
7. **Cost observability** — видишь стоимость каждого payment
8. **Revenue recovery** — автоматический retry failed payments

## Hyperswitch (Rust, 45.3k stars)

- Multi-provider (Stripe, Adyen, PayPal, 100+)
- Intelligent routing, cost observability
- SaaS и Self-host
- PCI compliant

## Polar (10.3k stars)

- Billing для AI стартапов
- Usage-based, token-based pricing
- SDKs: Python, JavaScript, TypeScript

## Lago (10.7k stars)

- Event-driven metering
- Real-time pricing
- Клиенты: Mistral AI, Groq, PayPal
- $829M инвойсов/мес

## Итог

Payments & billing: composable (Hyperswitch), AI-first (Polar), usage-based (Lago). Ключевая идея: не строить billing с нуля, а использовать open source платформу.