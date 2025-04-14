# 🏛️ Hermes - TikTok Username Monitor

![Hermes Banner](https://img.shields.io/badge/HERMES-TikTok%20Username%20Monitor-cyan?style=for-the-badge)
![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> Named after the swift messenger of the Greek gods, Hermes monitors TikTok for usernames of specified length.

## 📜 Overview

Hermes is a powerful, user-friendly TikTok username monitoring tool designed to help you discover available usernames of specific lengths. With its beautiful colored interface and advanced features, Hermes makes monitoring TikTok usernames easy and efficient.
## ✨ Features

- **Beautiful Colored Terminal Interface**: Vibrant, easy-to-navigate menus and displays
- **Multiple Monitoring Methods**:
  - Trending feed monitoring
  - Keyword-based search
  - Suggested users scanning
- **Advanced Capabilities**:
  - Proxy support with auto-rotation
  - User agent rotation to avoid detection
  - Rate limit detection and mitigation
  - Detailed statistics and logging
- **Convenient Tools**:
  - Save and load found usernames
  - Export functionality
  - Customizable username length target (3-5 characters)

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- Windows, macOS, or Linux

### Installation

#### Method 1: Using setup.bat (Windows)

1. Clone or download this repository
2. Run `setup.bat` to install all required dependencies
3. Run `start.bat` to launch Hermes

#### Method 2: Manual Installation

1. Clone or download this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run Hermes:
   ```
   python hermes.py
   ```

## 📖 Usage

After launching Hermes, you'll be presented with a menu offering various monitoring options:

1. **Monitor trending feed continuously** - Continuously checks TikTok's trending feed for usernames
2. **Search for usernames by keywords** - Uses keywords to find relevant usernames
3. **Check suggested users** - Scans TikTok's suggested users
4. **View found usernames** - Lists all usernames found so far
5. **Change target username length** - Adjust the length of usernames you're looking for
6. **Load proxies** - Add proxy support to avoid rate limiting
7. **Settings** - Configure various options

### Proxy Support

To use proxies with Hermes:
1. Create a text file with one proxy per line in format `ip:port` or `ip:port:username:password`
2. Select "Load proxies" from the menu and enter the file path

### Exporting Results

Found usernames can be exported to a text file by selecting "Export found usernames" in the Settings menu.

## 📋 Tips for Effective Monitoring

- Use proxies to avoid rate limiting
- Try different keywords related to your interests
- Monitor during peak hours for increased user activity
- For rare usernames, increase monitoring duration

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational purposes only. Please use responsibly and in accordance with TikTok's Terms of Service. The developers are not responsible for any misuse of this software.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📬 Contact

Have questions or suggestions? Open an issue on this repository.

---

*Hermes: Swift as thought, the messenger between worlds.*