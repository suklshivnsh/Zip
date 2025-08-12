#!/usr/bin/env python3
"""
Setup script for the Telegram Zip Extraction Bot
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'pyrogram', 'tgcrypto', 'aiohttp', 'aiofiles', 
        'ffmpeg', 'magic', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

def check_configuration():
    """Check bot configuration"""
    print("\n🔧 Checking configuration...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("💡 Copy .env.example to .env and edit with your bot credentials")
        return False
    
    # Load environment variables from .env if it exists
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Check required configuration
    required_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var, '')
        if not value or value in ['your_api_id', 'your_api_hash', 'your_bot_token', '0']:
            missing_vars.append(var)
            print(f"❌ {var}: Not set or using placeholder value")
        else:
            print(f"✅ {var}: Configured")
    
    if missing_vars:
        print(f"\n⚠️  Missing configuration: {', '.join(missing_vars)}")
        print("📖 See README.md for setup instructions")
        return False
    
    print("\n✅ Configuration looks good!")
    return True

def check_directories():
    """Check if required directories exist or can be created"""
    print("\n📁 Checking directories...")
    
    directories = ['downloads', 'extracted']
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        try:
            dir_path.mkdir(exist_ok=True)
            print(f"✅ {dir_name}/ directory ready")
        except Exception as e:
            print(f"❌ Failed to create {dir_name}/ directory: {e}")
            return False
    
    return True

def run_basic_test():
    """Run a basic functionality test"""
    print("\n🧪 Running basic functionality test...")
    
    try:
        from file_handler import FileHandler
        from config import Config
        
        # Test episode detection
        handler = FileHandler("./downloads", "./extracted")
        
        test_filename = "Test Show E05.mkv"
        episode = handler.detect_episode_number(test_filename)
        
        if episode == 5:
            print("✅ Episode detection working")
        else:
            print(f"❌ Episode detection failed: got {episode}, expected 5")
            return False
        
        # Test configuration validation (should fail with default values)
        if not Config.validate():
            print("✅ Configuration validation working")
        else:
            print("⚠️  Configuration validation allowing empty values")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "="*60)
    print("🚀 Setup Complete! Next Steps:")
    print("="*60)
    print()
    print("1. 📱 Create a Telegram Bot:")
    print("   • Message @BotFather on Telegram")
    print("   • Use /newbot command")
    print("   • Get your bot token")
    print()
    print("2. 🔑 Get Telegram API credentials:")
    print("   • Visit https://my.telegram.org")
    print("   • Get your API ID and API Hash")
    print()
    print("3. ⚙️  Configure the bot:")
    print("   • Edit .env file with your credentials")
    print("   • Set API_ID, API_HASH, and BOT_TOKEN")
    print()
    print("4. 🏃 Run the bot:")
    print("   • python main.py")
    print()
    print("5. 💬 Test the bot:")
    print("   • Send /start to your bot on Telegram")
    print("   • Try uploading a zip file")
    print("   • Use /e command with a pattern")
    print()
    print("📖 For detailed instructions, see README.md")
    print("="*60)

def main():
    """Main setup function"""
    print("🤖 Telegram Zip Extraction Bot - Setup\n")
    
    all_checks_passed = True
    
    # Run all checks
    if not check_dependencies():
        all_checks_passed = False
    
    if not check_configuration():
        all_checks_passed = False
    
    if not check_directories():
        all_checks_passed = False
    
    if all_checks_passed:
        if not run_basic_test():
            all_checks_passed = False
    
    if all_checks_passed:
        print("\n🎉 Setup completed successfully!")
        show_next_steps()
        return 0
    else:
        print("\n❌ Setup incomplete. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())