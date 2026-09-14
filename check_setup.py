"""
Quick Setup Checker for Company X Dashboard
Run this before starting the dashboard to verify everything is ready
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.8+")
        return False

def check_packages():
    """Check required packages"""
    print("\n🔍 Checking required packages...")
    packages = [
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'sklearn',
        'seaborn',
        'matplotlib'
    ]

    all_ok = True
    for package in packages:
        try:
            __import__(package)
            print(f"   ✅ {package} - Installed")
        except ImportError:
            print(f"   ❌ {package} - NOT installed")
            all_ok = False

    if not all_ok:
        print("\n   💡 Fix: Run 'pip install -r requirements.txt'")

    return all_ok

def check_data_files():
    """Check if data files exist"""
    print("\n🔍 Checking data files...")
    base_path = Path(__file__).parent

    required_files = [
        'cards_data.csv',
        'users_data.csv',
        'train_fraud_labels.csv',
        'mcc_codes.csv'
    ]

    sample_files = [
        'transactions_data_25pc.csv',
        'transactions_data_10pc.csv',
        'transactions_data.csv'
    ]

    all_ok = True

    # Check required files
    for file in required_files:
        file_path = base_path / file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {file} - {size_mb:.1f} MB")
        else:
            print(f"   ❌ {file} - NOT FOUND")
            all_ok = False

    # Check at least one transaction file exists
    trans_found = False
    for file in sample_files:
        file_path = base_path / file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {file} - {size_mb:.1f} MB")
            trans_found = True

    if not trans_found:
        print(f"   ❌ No transaction data file found!")
        print(f"   💡 Need at least one of: {', '.join(sample_files)}")
        all_ok = False

    return all_ok

def check_project_structure():
    """Check if project structure is correct"""
    print("\n🔍 Checking project structure...")
    base_path = Path(__file__).parent

    required_items = [
        ('app.py', 'file'),
        ('requirements.txt', 'file'),
        ('utils', 'dir'),
        ('utils/data_loader.py', 'file'),
        ('utils/segmentation.py', 'file'),
        ('utils/visualizations.py', 'file')
    ]

    all_ok = True
    for item, item_type in required_items:
        item_path = base_path / item
        if item_type == 'file':
            if item_path.is_file():
                print(f"   ✅ {item}")
            else:
                print(f"   ❌ {item} - Missing")
                all_ok = False
        elif item_type == 'dir':
            if item_path.is_dir():
                print(f"   ✅ {item}/")
            else:
                print(f"   ❌ {item}/ - Missing")
                all_ok = False

    return all_ok

def main():
    """Run all checks"""
    print("=" * 60)
    print("Company X Dashboard - Setup Checker")
    print("=" * 60)

    checks = [
        check_python_version(),
        check_packages(),
        check_data_files(),
        check_project_structure()
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print("✅ ALL CHECKS PASSED!")
        print("\n🚀 You're ready to run the dashboard:")
        print("   streamlit run app.py")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\n💡 Please fix the issues above before running the dashboard")
    print("=" * 60)

if __name__ == "__main__":
    main()
