#!/usr/bin/env python3
"""Quick script to check GPU availability for Cellpose."""

def check_gpu():
    print("Checking GPU availability for Cellpose...")
    print("=" * 60)

    try:
        import torch
        print(f"✓ PyTorch installed: {torch.__version__}")

        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.version.cuda}")
            print(f"✓ GPU device: {torch.cuda.get_device_name(0)}")
            print(f"✓ Number of GPUs: {torch.cuda.device_count()}")

            # Test GPU
            try:
                x = torch.tensor([1.0]).cuda()
                print(f"✓ GPU test successful")
                return True
            except Exception as e:
                print(f"✗ GPU test failed: {e}")
                return False
        else:
            print("✗ CUDA not available")
            print("\nTo install CUDA support:")
            print("  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
            return False

    except ImportError:
        print("✗ PyTorch not installed")
        print("\nInstall PyTorch with CUDA:")
        print("  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
        return False

if __name__ == "__main__":
    import sys
    has_gpu = check_gpu()
    print("=" * 60)
    if has_gpu:
        print("✓ GPU is ready for Cellpose!")
    else:
        print("⚠ GPU not available - Cellpose will use CPU (much slower)")
    sys.exit(0 if has_gpu else 1)
