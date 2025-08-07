import subprocess
import sys
import os
import venv
import requests

# --- Configuration ---
# 🔑 Replace with your actual YouTube API key. Leave as is if you don't have one.
YOUTUBE_API_KEY = "AIzaSyC7MHdyOtsFaUPS7iYBAl9YoFqA7JLjYlk"
VENV_NAME = "venv"  # The name for the virtual environment folder

# --- Environment Detection ---
# Detect if the script is running in a Google Colab environment.
IN_COLAB = 'google.colab' in sys.modules

def is_windows():
    """Checks if the current operating system is Windows."""
    return os.name == 'nt'

def get_pip_command_args():
    """
    Determines the correct command for running pip.
    Returns a list of arguments for subprocess.
    """
    if IN_COLAB:
        # In Colab, it's best to use the system's pip tied to the current Python executable.
        return [sys.executable, '-m', 'pip']
    else:
        # On a local machine, use the pip from the virtual environment.
        venv_path = os.path.abspath(VENV_NAME)
        if is_windows():
            pip_exec = os.path.join(venv_path, 'Scripts', 'pip.exe')
        else:
            pip_exec = os.path.join(venv_path, 'bin', 'pip')
        
        # Before returning, check if the pip executable actually exists.
        if not os.path.exists(pip_exec):
            print(f"❌ Critical Error: Pip executable not found at '{pip_exec}'.")
            print("   The virtual environment might be corrupted or wasn't created properly.")
            print("   Try deleting the 'venv' folder and running the script again.")
            sys.exit(1)
        return [pip_exec]

def create_virtual_environment():
    """
    Creates a virtual environment unless running in Colab.
    """
    if IN_COLAB:
        print("👍 Running in Google Colab, skipping virtual environment creation.")
        return

    if not os.path.exists(VENV_NAME):
        print(f"🌱 Creating virtual environment: '{VENV_NAME}'...")
        try:
            venv.create(VENV_NAME, with_pip=True)
            print("✅ Virtual environment created successfully.")
        except Exception as e:
            print(f"❌ Critical Error: Could not create virtual environment: {e}")
            sys.exit(1)
    else:
        print(f"👍 Virtual environment '{VENV_NAME}' already exists.")

def install_libraries(libraries, pip_cmd_args):
    """
    Installs a list of specified libraries.
    """
    if not libraries:
        print("🤷 No libraries were provided to install.")
        return

    print(f"\n🔧 Attempting to install: {', '.join(libraries)}")
    for lib in libraries:
        print(f"--- Installing {lib} ---")
        try:
            command = pip_cmd_args + ['install', lib]
            result = subprocess.run(
                command,
                capture_output=True, text=True, check=True, encoding='utf-8'
            )
            print(result.stdout)
            print(f"✅ Successfully installed: {lib}")
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.strip()
            print(f"❌ Error installing '{lib}'.")
            print("🔍 Full Error Log:")
            print(error_message)
            suggest_fix(lib, error_message)
            get_youtube_help(lib)
        print("-" * (len(lib) + 20))


def install_from_requirements(pip_cmd_args):
    """
    Installs all libraries listed in a 'requirements.txt' file.
    """
    if not os.path.exists('requirements.txt'):
        print("📄 'requirements.txt' not found. Please create one or choose another option.")
        return

    print("🔧 Installing all libraries from requirements.txt...")
    try:
        command = pip_cmd_args + ['install', '-r', 'requirements.txt']
        result = subprocess.run(
            command,
            capture_output=True, text=True, check=True, encoding='utf-8'
        )
        print(result.stdout)
        print("✅ Successfully installed all libraries from requirements.txt.")
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip()
        print("❌ An error occurred while installing from requirements.txt.")
        print("🔍 Full Error Log:", error_message)
        suggest_fix("libraries from requirements.txt", error_message)

def generate_requirements_file(pip_cmd_args):
    """
    Generates a requirements.txt file by 'freezing' the current environment's packages.
    """
    print("📝 Generating requirements.txt...")
    try:
        command = pip_cmd_args + ['freeze']
        result = subprocess.run(
            command,
            capture_output=True, text=True, check=True, encoding='utf-8'
        )
        with open('requirements.txt', 'w') as f:
            f.write(result.stdout)
        print("✅ requirements.txt has been generated successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ Failed to generate requirements.txt.")
        print("🔍 Error message:", e.stderr.strip())

def suggest_fix(library, error_message):
    """
    Provides specific, context-aware suggestions for common installation errors.
    """
    print("\n💡 Suggested Fix:")
    if 'permission denied' in error_message.lower():
        advice = "Try running your terminal or command prompt as an Administrator (Windows) or using `sudo` (macOS/Linux)."
        print(f"👉 Permission Error: {advice}")
    elif 'failed building wheel' in error_message.lower():
        print("🛠️ Build Error: This package needs to compile from source. You might be missing system-level build tools.")
        print("   - On Debian/Ubuntu: `sudo apt-get install build-essential python3-dev`")
        print("   - On Fedora/CentOS: `sudo yum groupinstall 'Development Tools'`")
        print("   - Also, try upgrading pip and installing wheel: `pip install --upgrade pip wheel`")
    elif 'no matching distribution found' in error_message.lower():
        print(f"🔎 Not Found: Could not find a package named '{library}'. Double-check for typos.")
    elif 'requires python' in error_message.lower():
        print(f"🐍 Version Mismatch: This version of '{library}' is not compatible with your Python version ({sys.version.split()[0]}).")
    else:
        search_query = f"pip install {library} error {error_message.splitlines()[-1]}"
        print(f"❓ No specific fix found. Try searching online for the following query:")
        print(f"   \"{search_query}\"")


def get_youtube_help(lib_name):
    """
    Fetches a relevant YouTube tutorial for installing the specified library.
    """
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY":
        print("\n⚠️ YouTube help skipped (API key not provided).")
        return

    print("\n🎥 Searching for a YouTube tutorial...")
    query = f"How to install {lib_name} Python"
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={YOUTUBE_API_KEY}&maxResults=1&type=video"

    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data.get('items'):
            video_id = data['items'][0]['id']['videoId']
            video_title = data['items'][0]['snippet']['title']
            print(f"▶️  Found Video: {video_title}")
            print(f"🔗 https://www.youtube.com/watch?v={video_id}")
        else:
            print("⚠️ No relevant video found on YouTube.")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ YouTube lookup failed: {e}")

def main():
    """Main function to run the interactive command-line menu."""
    print("="*50)
    print("🐍 Advanced Python Library & Environment Manager 🐍")
    print("="*50)

    create_virtual_environment()
    pip_command_args = get_pip_command_args()

    while True:
        print("\n--- Menu ---")
        if IN_COLAB:
            print("Environment: Google Colab Session")
        else:
            print(f"Environment: ./{VENV_NAME}/")
        print("1. Install new libraries manually")
        print("2. Install all libraries from requirements.txt")
        print("3. Generate requirements.txt from current environment")
        print("4. Exit")
        choice = input("👉 Enter your choice (1-4): ")

        if choice == '1':
            libs_str = input("📦 Enter libraries to install (comma-separated): ")
            libs = [lib.strip() for lib in libs_str.split(',') if lib.strip()]
            install_libraries(libs, pip_command_args)
        elif choice == '2':
            install_from_requirements(pip_command_args)
        elif choice == '3':
            generate_requirements_file(pip_command_args)
        elif choice == '4':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select a number from 1 to 4.")

if __name__ == "__main__":
    main()