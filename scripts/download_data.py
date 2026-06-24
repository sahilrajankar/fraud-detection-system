"""
Download IEEE-CIS Fraud Detection Dataset
"""

import os
import sys

print("=" * 80)
print("IEEE-CIS Fraud Detection Dataset Downloader")
print("=" * 80)
print()

# Check if kaggle is installed
try:
    import kaggle
    print("✓ Kaggle API found")
except ImportError:
    print("❌ Kaggle API not installed")
    print("Install it: pip install kaggle")
    sys.exit(1)

# Check for Kaggle credentials
kaggle_dir = os.path.expanduser("~/.kaggle")
kaggle_json = os.path.join(kaggle_dir, "kaggle.json")

if not os.path.exists(kaggle_json):
    print("❌ Kaggle credentials not found")
    print()
    print("Setup instructions:")
    print("1. Go to https://www.kaggle.com/settings")
    print("2. Click 'Create New API Token'")
    print("3. Save kaggle.json to:", kaggle_dir)
    print()
    sys.exit(1)

print("✓ Kaggle credentials found")
print()

# Create data directory
data_dir = "data/raw"
os.makedirs(data_dir, exist_ok=True)

print("Downloading IEEE-CIS Fraud Detection dataset...")
print("This may take a few minutes...")
print()

try:
    # Download dataset
    os.system("kaggle competitions download -c ieee-fraud-detection -p data/raw")
    
    print()
    print("✓ Download complete")
    print()
    print("Extracting files...")
    
    # Extract files
    import zipfile
    
    zip_path = "data/raw/ieee-fraud-detection.zip"
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("data/raw")
        
        print("✓ Extraction complete")
        print()
        print("Files available:")
        for file in os.listdir("data/raw"):
            if file.endswith('.csv'):
                file_path = os.path.join("data/raw", file)
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"  - {file} ({size_mb:.1f} MB)")
        
        # Clean up zip
        os.remove(zip_path)
        print()
        print("✅ Dataset ready in data/raw/")
    else:
        print("❌ Download may have failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Manual download option:")
    print("1. Go to https://www.kaggle.com/c/ieee-fraud-detection/data")
    print("2. Download all files")
    print("3. Extract to: data/raw/")
    sys.exit(1)
