# NVIDIA-first decision record

The NVIDIA option is listed first for every layer. "Running today" means there is code in this repo that does it. Nothing below claims NVIDIA usage that is not in code.

What runs today (OBSERVED):
- `beatoven/media_intel/providers/clip_provider.py:34-35` selects `cuda` when PyTorch reports it and loads `openai/clip-vit-base-patch32`. That is PyTorch on an NVIDIA GPU when one is present, else CPU.
- `beatoven/gpu/device_utils.py` and `beatoven/gpu/runpod_launcher.py` select a device and launch a rented GPU.
- No NVIDIA SDK, NIM, Triton, Riva or TensorRT call exists in the repo (grep, `main@59312f5`).
- The motif engine named in the Canon Fold-In Seal has no code in the repo.

| Layer | NVIDIA option | Alternatives | Decision | Reason |
|---|---|---|---|---|
| Model: scene tagging (media_intel CLIP provider) | NV-CLIP via NIM | `openai/clip-vit-base-patch32` on PyTorch (running today); SigLIP | **Keep current; NV-CLIP evaluating** | The current provider works and already uses CUDA when present. No measured accuracy or latency gap justifies a swap. |
| Model: motif engine training | PyTorch on NVIDIA GPUs (CUDA), mixed precision | Apple MPS; CPU | **Planned: NVIDIA GPU** | No training code exists yet. CUDA is the default path `beatoven/docs/gpu.md` already documents. Nothing to claim until code exists. |
| Serving | Triton Inference Server, or NIM microservices | In-process PyTorch behind FastAPI (running today) | **Keep in-process; Triton evaluating** | One small model, one process. A model server is unjustified until there is more than one model or a latency target. |
| Eval | NVIDIA NeMo Evaluator | pytest determinism and golden tests (running today) | **Keep pytest** | The properties that matter here are byte-identical output and bounded values. Those are assertions, not model-quality scores. |
| Data | RAPIDS (cuDF) | Plain Python and NumPy (running today) | **Rejected for now** | Inputs are single JSON documents of a few kilobytes. There is no dataframe workload. |
| Speech / audio | Riva; NVIDIA Maxine | librosa and the `audio_provider` heuristics (running today); Demucs for stems | **Not needed now; Riva evaluating if speech input is added** | No speech feature exists or is specified. |
| Output Module firmware (MCU) | None | RP2350 (chosen), STM32, Daisy Patch SM | **REJECTED for NVIDIA** | There is no NVIDIA MCU-class part. The smallest NVIDIA compute module is a Jetson, which is a Linux computer drawing watts, not a microcontroller for a ≤ 120 mA Eurorack Module. |
| Host driver and Output Stream compiler | None applicable | Pure Python, integer math | **REJECTED for NVIDIA** | Deterministic integer scheduling. A GPU adds nothing and floating-point variation across devices would harm SEED determinism. |

`[NEEDS CLARIFICATION: is an NVIDIA Inception or partner commitment driving a required NVIDIA component? If so, name the layer.]`
