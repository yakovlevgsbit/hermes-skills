# AnyModel Models — Coefficients & Selection

Data: 2026-10-20, 104 models

Formula: Raw tokens × coefficient = balance tokens

## Free (coefficient = 0)

| ID | Context | Use Case |
|----|---------|----------|
| am/free | — | Auto-router |
| am/gpt-oss-20b | 131K | Open source, code |
| am/nemotron-3-ultra-550b-a55b | 262K | Large context |
| am/nemotron-3-super-120b-a12b | 262K | |
| am/nemotron-3.5-lightning-30b-a3b | 262K | |
| am/laguna-xs-2.1 | 131K | |
| am/llama-3.2-11b-vision-instruct | 131K | Vision |
| am/nemotron-3-nano-omni-30b-a3b-reasoning | 262K | |
| am/diffusiongemma-26b-a4b-it | 131K | |
| am/riva-translate-4b-instruct-v2 | 8K | Translation |
| am/nemotron-3.5-content-safety | 32K | Moderation |
| am/flux.2-klein-4b | — | Image gen |

## Ultra-cheap (0.25-0.3)

| ID | Coeff | Context | Use Case |
|----|-------|---------|----------|
| ds/deepseek-v4-flash | 0.25 | 1M | Fast, long context |
| qwen/qwen3.8-max | 0.25 | 1M | Multilingual |
| qwen/qwen3.7-max | 0.25 | 1M | |
| qwen/qwen3.7-plus | 0.25 | 1M | |
| glm/glm-4.7 | 0.3 | 200K | Balanced |
| glm/glm-4.6v | 0.3 | 128K | |

## Cheap (0.5-0.75)

| ID | Coeff | Context |
|----|-------|---------|
| ag/gpt-oss-120b-medium | 0.5 | 128K |
| am/minimax-m3 | 0.5 | 512K |
| kmc/k2.6 | 0.5 | 262K |
| xai/grok-build-0.1 | 0.5 | 256K |
| glm/glm-5 | 0.5 | 200K |
| ds/deepseek-v4-pro | 0.5 | 1M |
| glm/glm-5.3-flash | 0.5 | — |
| flow/nano-banana-lite | 0.75 | — |
| cx/gpt-6-luna | 0.75 | 1M |

## Medium (1-1.5)

| ID | Coeff | Context |
|----|-------|---------|
| nano-banana-lite | 1 | — |
| nano-banana | 1 | — |
| nano-banana-pro | 1 | — |
| xai/grok-4.3 | 1 | 1M |
| xai/grok-4.20-0309-reasoning | 1 | 1M |
| pg/gemini-4-argon | 1 | 1M |
| cx/gpt-image-2.5 | 1.25 | — |
| cx/gpt-5.6-terra | 1.5 | 1M |
| kmc/kimi-for-coding | 1.5 | 262K |
| glm/glm-5.3 | 1.5 | — |

## Expensive (2-3)

| ID | Coeff | Context |
|----|-------|---------|
| cc/claude-haiku-4-5-20251001 | 1.6 | 200K |
| ag/gemini-pro-agent | 1.7 | 1M |
| cx/gpt-6.1-sol | 2 | 1M |
| xai/grok-4.7 | 2 | 500K |
| ag/claude-sonnet-4-6 | 2.4 | 1M |
| cx/gpt-5.6-sol | 2.5 | 1M |
| kmc/k3 | 3 | 262K |
| cc/claude-sonnet-5 | 3 | 1M |

## Very expensive (4-6)

| ID | Coeff | Context |
|----|-------|---------|
| krea/k2-turbo | 3.9 | — |
| cx/gpt-6-astra | 4 | 1M |
| cc/claude-opus-4-8 | 4 | 1M |
| cc/claude-opus-5-5 | 6 | 1M |
| cc/claude-opus-5 | 6 | 1M |

## Gemini Flash (0.6, 1M context)

ag/gemini-3.8-flash-high, ag/gemini-3.8-flash-medium, ag/gemini-3.8-flash-low
ag/gemini-3.6-flash-high, ag/gemini-3.6-flash-medium, ag/gemini-3.6-flash-low
ag/gemini-3-flash, ag/gemini-2.5-flash, ag/gemini-2.5-flash-lite

## Image/Video models (expensive)

| ID | Coeff | Type |
|----|-------|------|
| anymedia/seedream-4.5 | 7.35 | image |
| krea/k2-medium | 7.8 | image |
| krea/seedream-4 | 7.8 | image |
| anymedia/nano-banana-2 | 9.8 | image |
| krea/flux-1.1-pro | 10.4 | image |
| krea/nano-banana | 11.15 | image |
| anymedia/gpt-image-2 | 23.03 | image |
| krea/nano-banana-pro | 39 | image |

## Balance Token Estimation (5M balance tokens)

| Strategy | Model | Requests (2K raw each) |
|----------|-------|------------------------|
| Maximum economy | ds/deepseek-v4-flash | ~10,000 |
| Balanced | glm/glm-5 | ~5,000 |
| Universal | am/free | ~2,500-5,000 |
| Premium | cc/claude-sonnet-5 | ~830 |

## Recommended by Use Case

- **Bots & automation**: ds/deepseek-v4-flash (×0.25, 1M context)
- **Content**: glm/glm-5 (×0.5, Russian language)
- **Complex tasks**: am/free (router) or cc/claude-sonnet-4-6 (×2.4)
- **Images**: am/flux.2-klein-4b (free)