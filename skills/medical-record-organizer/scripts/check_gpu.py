#!/usr/bin/env python3
"""Detect GPU availability and PaddlePaddle GPU status. Output JSON to stdout."""

import json
import re
import shutil
import subprocess
import sys


def get_cuda_version() -> str | None:
    """Get CUDA version from nvidia-smi output."""
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return None
    try:
        out = subprocess.check_output(
            [nvidia_smi], stderr=subprocess.DEVNULL, timeout=10
        ).decode("utf-8", errors="replace")
        m = re.search(r"CUDA Version:\s*([\d.]+)", out)
        return m.group(1) if m else None
    except Exception:
        return None


def get_paddle_info() -> tuple[str | None, bool]:
    """Return (paddle_version, is_gpu_enabled)."""
    try:
        import paddle

        version = paddle.__version__
        gpu_enabled = paddle.device.is_compiled_with_cuda()
        return version, gpu_enabled
    except ImportError:
        return None, False
    except Exception:
        return None, False


def build_install_command(cuda_version: str) -> str:
    """Build pip install command with the correct PaddlePaddle index URL."""
    major_minor = cuda_version.split(".")
    major = int(major_minor[0]) if major_minor else 0

    if major <= 11:
        cuda_tag = "cu118"
    else:
        # CUDA 12.x — prefer cu126; fall back to cu121 if needed
        minor = int(major_minor[1]) if len(major_minor) > 1 else 0
        if minor >= 6:
            cuda_tag = "cu126"
        else:
            cuda_tag = "cu121"

    index_url = f"https://www.paddlepaddle.org.cn/packages/stable/{cuda_tag}/"
    return (
        f"pip install --upgrade paddlepaddle-gpu "
        f"-i {index_url}"
    )


def check() -> dict:
    cuda_version = get_cuda_version()
    paddle_version, paddle_gpu = get_paddle_info()

    result = {
        "gpu_available": cuda_version is not None,
        "cuda_version": cuda_version,
        "paddle_version": paddle_version,
        "paddle_gpu_enabled": paddle_gpu,
        "status": "ok",
        "message": "",
        "install_command": None,
    }

    # --- no_gpu ---------------------------------------------------------
    if cuda_version is None:
        result["status"] = "no_gpu"
        result["message"] = (
            "未检测到 NVIDIA GPU（nvidia-smi 不可用），当前为 CPU 模式。"
        )
        return result

    # --- version_mismatch: paddle < 3.0 ---------------------------------
    if paddle_version:
        try:
            major = int(paddle_version.split(".")[0])
        except (ValueError, IndexError):
            major = 0
        if major < 3:
            cmd = build_install_command(cuda_version)
            result["status"] = "version_mismatch"
            result["message"] = (
                f"PaddlePaddle {paddle_version} 版本低于 3.0，"
                f"PaddleX 3.x 需要 PaddlePaddle >= 3.0。"
            )
            result["install_command"] = cmd
            return result

    # --- gpu_not_enabled: GPU exists but paddle not compiled with CUDA ---
    if not paddle_gpu:
        cmd = build_install_command(cuda_version)
        result["status"] = "gpu_not_enabled"
        result["message"] = (
            f"检测到 GPU (CUDA {cuda_version})，"
            f"但当前 PaddlePaddle{' ' + paddle_version if paddle_version else ''} 未启用 GPU。"
        )
        result["install_command"] = cmd
        return result

    # --- ok --------------------------------------------------------------
    result["message"] = (
        f"PaddlePaddle {paddle_version} GPU 已启用 (CUDA {cuda_version})"
    )
    return result


if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False, indent=2))
