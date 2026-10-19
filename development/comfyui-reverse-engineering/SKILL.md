---
name: comfyui-reverse-engineering
description: "Use when working with diffusion models or node graphs."
---

# ComfyUI — Reverse-Engineering Analysis

GitHub: https://github.com/Comfy-Org/ComfyUI
ComfyUI License (source-available), ~65k stars. Python 3.10+.

> **Полный разбор** (977 файлов, детали): `/root/kb/projects/comfyui-reverse-engineering.md`

## Architecture

```
Frontend (Vue/TS, PyPI)
  ↕ HTTP + WebSocket
server.py (1591 lines) — aiohttp
  ├─ /ws (binary events: progress, preview, status)
  ├─ /prompt (submit workflow)
  ├─ /history, /view, /object_info
  └─ /internal/* (frontend-only)
execution.py (1465 lines)
  ├─ DynamicPrompt → graph traversal → cache → node execution
  ├─ HierarchicalCache / LRUCache / RAMPressureCache
  ├─ ExecutionBlocker (conditional execution)
  └─ Async/await, asyncio.Task per node
nodes.py (2630 lines) — built-in nodes
comfy_extras/ (144 files) — Flux, SD3, Qwen, Wan, etc.
comfy/ldm/ — model implementations
api_server/ — REST API
app/ — UserManager, ModelManager, Governance
```

## Node System

Каждая нода — Python-класс:

```python
class CLIPTextEncode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="CLIPTextEncode",
            category="model/conditioning",
            inputs=[io.String.Input("text"), io.Clip.Input("clip")],
            outputs=[io.Conditioning.Output()],
        )
    @classmethod
    def execute(cls, clip, text) -> io.NodeOutput:
        tokens = clip.tokenize(text)
        return io.NodeOutput(clip.encode_from_tokens_scheduled(tokens))
```

### IO Types

IO.STRING, IO.INT, IO.FLOAT, IO.BOOLEAN, IO.Image, IO.Latent, IO.Conditioning, IO.Clip, IO.Vae, IO.Model, IO.Combo, IO.Sigmas, IO.Mask, IO.ControlNet

### Hidden inputs (automatic)

PROMPT (workflow JSON), EXTRA_PNGINFO (metadata), UNIQUE_ID, EXECUTION_LIST

### Categories

model/loaders, model/conditioning, model/sampling/schedulers, model/sampling/samplers, model/latent, image, video, mask, controlnet

## Caching

| Type | Flag | Behavior |
|------|------|----------|
| HierarchicalCache | default | Aggressive — dump data ASAP |
| LRUCache | --cache-lru N | Last N results in memory |
| RAMPressureCache | --cache-ram | By RAM threshold |
| NullCache | --cache-none | No cache, min RAM/VRAM |

## Model Support

### Image: SD 1.5, SDXL, SD3.5, Flux.1, Flux.2, Qwen Image, Z-Image, Hunyuan Image 2.1, HiDream, Lumina Image 2.0, Chroma, Anima, LongCat Image, Ideogram 4, Krea 2, MageFlow, Kandinsky 5, Ernie Image

### Video: Wan 2.1/2.2, LTX-Video 2/2.3, HunyuanVideo 1.5, Kandinsky 5 Video, CogVideoX, Cosmos Predict2, Bernini-R, SCAIL 2, Mochi

### Audio: ACE-Step 1.5, Stable Audio 3, MiniMax Music 3, Yue 2, MiniMax H3

### 3D/Vision: Hunyuan3D 2.1, TripoSplat, SeedVR2, SUPIR, Depth Anything 3, MoGe, SAM 3/3.1, RT-DETRv4, BiRefNet

### Text: Gemma 3/4, Qwen3/3.5/3-VL

## Key Patterns

1. **Node-based graph execution** — define_schema() + execute(). Graph → JSON → execution.
2. **Multi-level caching** — CacheKeySetInputSignature + HierarchicalCache. Partial re-execution.
3. **WebSocket binary events** — progress, preview, status. For any long-running process.
4. **Hidden inputs** — automatic PROMPT, EXTRA_PNGINFO, UNIQUE_ID per node.
5. **DynamicVRAM** — auto offload unused layers. NVIDIA + AMD (ROCm 7.14+).
6. **ExecutionBlocker** — conditional execution without branching.
7. **Asset management** — blake3 hashing + SQLite + background scanning.
8. **Origin-only middleware** — cross-site WebSocket hijacking protection.
9. **PNG metadata embedding** — workflow + seed in PNG. Recover workflow from image.
10. **Extension system** — ComfyExtension + get_node_list() + comfy_entrypoint().

## Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /prompt | POST | Submit workflow |
| /history | GET | Results history |
| /history/{id} | GET | Specific result |
| /view | GET | Get image |
| /queue | GET | Queue status |
| /interrupt | POST | Cancel execution |
| /object_info | GET | Node schemas |
| /ws | WS | Real-time updates |

## Installation

```bash
git clone https://github.com/Comfy-Org/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
python main.py
# Desktop app: https://www.comfy.org/download
# Windows portable: releases/latest/download/ComfyUI_windows_portable_nvidia.7z
```

## Key CLI Flags

--listen, --port, --cuda-device, --force-fp16, --force-fp32, --bf16-unet, --cache-ram, --cache-lru, --cache-none, --preview-method, --enable-cors-header, --auto-launch, --offline, --disable-all-custom-nodes, --enable-dynamic-vram, --vram-headroom