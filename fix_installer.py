import subprocess
import sys

def install_package(package_name):
    print(f"Attempting to install: {package_name}...")
    try:
        # This forces Python to use its own internal installer
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ SUCCESS: {package_name} is installed!")
    except Exception as e:
        print(f"❌ ERROR: Could not install {package_name}. Reason: {e}")

if __name__ == "__main__":
    print("--- STARTING AUTOMATIC REPAIR ---")
    # We install lxml (the one you are missing)
    install_package("lxml")
    # We also install a backup option just in case
    install_package("html5lib") 
    print("\n--- REPAIR FINISHED ---")
    print("You can now try running your analyze_results.py script again.")
    input("Press Enter to close this window...")