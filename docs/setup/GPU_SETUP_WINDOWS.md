# GPU Acceleration Setup for Cellpose on Windows

This guide will help you set up GPU acceleration for Cellpose on Windows, which can significantly speed up cell segmentation (often 10-50x faster than CPU).

## Prerequisites

### 1. Check if you have an NVIDIA GPU

Open Command Prompt and run:
```bash
nvidia-smi
```

If this command works and shows your GPU information, you have an NVIDIA GPU and can proceed. If not, GPU acceleration is not available on your system.

### 2. Check CUDA Compatibility

Note the CUDA version shown in the `nvidia-smi` output (top right). You need CUDA 11.8 or higher for the configuration below.

If your CUDA version is lower than 11.8, you may need to:
- Update your NVIDIA drivers (recommended): https://www.nvidia.com/Download/index.aspx
- Or use an older PyTorch version compatible with your CUDA version

## Installation Steps

### Option 1: Fresh Installation (Recommended)

If you haven't installed Cellpose yet or want to start fresh:

1. **Remove existing cellpose_venv** (if it exists):
   ```bash
   rmdir /s cellpose_venv
   ```

2. **Create new virtual environment**:
   ```bash
   python -m venv cellpose_venv
   ```

3. **Activate the environment**:
   ```bash
   cellpose_venv\Scripts\activate
   ```

4. **Install GPU-enabled Cellpose**:
   ```bash
   pip install -r percell\setup\requirements_cellpose_gpu.txt
   ```

### Option 2: Upgrade Existing Installation

If you already have Cellpose installed and want to add GPU support:

1. **Activate your existing cellpose_venv**:
   ```bash
   cellpose_venv\Scripts\activate
   ```

2. **Uninstall CPU-only PyTorch**:
   ```bash
   pip uninstall torch torchvision torchaudio -y
   ```

3. **Install CUDA-enabled PyTorch**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

## Verify GPU Installation

After installation, verify that PyTorch can see your GPU:

```bash
cellpose_venv\Scripts\activate
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

You should see:
```
CUDA available: True
CUDA device: [Your GPU Name]
```

If you see `CUDA available: False`, there's an issue with the installation.

## Verify Cellpose GPU Support

Test that Cellpose can use the GPU:

```bash
cellpose_venv\Scripts\activate
python -c "from cellpose import core; print(f'Cellpose using GPU: {core.use_gpu()}')"
```

You should see:
```
Cellpose using GPU: True
```

## Troubleshooting

### CUDA available: False

**Possible causes:**
1. **Incompatible CUDA version**: Your GPU driver's CUDA version might not match PyTorch's requirements
   - **Solution**: Update NVIDIA drivers or install a different PyTorch version

2. **Wrong PyTorch version installed**: You might have the CPU-only version
   - **Solution**: Verify with `pip list | findstr torch` and reinstall if needed

3. **GPU not detected**: Hardware or driver issue
   - **Solution**: Run `nvidia-smi` to verify GPU is detected

### "ImportError: DLL load failed" or similar errors

**Solution**: Install/update Microsoft Visual C++ Redistributable:
- Download from: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist

### Out of Memory Errors

If you get CUDA out of memory errors:
- Reduce the batch size in Cellpose settings
- Process fewer/smaller images at a time
- Close other GPU-intensive applications

## CUDA Version Compatibility

If you need a different CUDA version, use these PyTorch installation commands:

**CUDA 12.1:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**CUDA 11.8:** (default in our requirements file)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**CPU only:** (fallback if GPU doesn't work)
```bash
pip install torch torchvision torchaudio
```

## Performance Comparison

You should see significant speedup with GPU acceleration:

| Hardware | Typical Processing Time (per image) |
|----------|-------------------------------------|
| CPU (Intel i7) | 30-60 seconds |
| GPU (RTX 3060) | 2-5 seconds |
| GPU (RTX 4090) | 1-3 seconds |

Actual performance depends on image size, complexity, and model parameters.

## Additional Resources

- PyTorch CUDA Installation: https://pytorch.org/get-started/locally/
- Cellpose GPU Documentation: https://cellpose.readthedocs.io/en/latest/installation.html
- NVIDIA Driver Downloads: https://www.nvidia.com/Download/index.aspx
