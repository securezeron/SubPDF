# 🚀 **SubPDF** 🚀

![SubPDF Logo](https://github.com/user-attachments/assets/2967421c-179b-4446-8230-336b0e8ecf32)


---

## 🌐 **Discover Hidden Domains & Subdomains from PDFs Effortlessly!**

**SubPDF** is a **sleek**, **powerful**, and **user-friendly** command-line tool designed to **extract domains and subdomains** from PDF files with lightning speed. Whether you're a cybersecurity analyst, data scientist, or simply managing extensive document repositories, SubPDF streamlines the process of uncovering valuable link information embedded within PDFs.

---

## 📌 **Table of Contents**

- [🌟 Features](#-features)
- [💻 Installation](#-installation)
- [🛠️ Usage](#️-usage)
  - [📚 Basic Commands](#-basic-commands)
  - [🔧 Advanced Options](#-advanced-options)
- [📈 Output Formats](#-output-formats)
- [🔥 Examples](#-examples)
- [📦 Dependencies](#-dependencies)
- [🤝 Contributing](#-contributing)
- [📝 License](#-license)
- [📞 Contact](#-contact)
- [🙏 Acknowledgements](#-acknowledgements)

---

## 🌟 **Features**

- **⚡ Multi-threaded Fast Processing:** Utilize multi-threading to handle numerous PDFs concurrently, drastically reducing processing time.
- **🔍 Comprehensive Link Extraction:** Extracts both **domains** and **subdomains** from clickable annotations and text within PDFs.
- **📂 Flexible Input Sources:** Accepts single URLs, direct PDF links, input lists (text files), and JSON files containing URLs.
- **🖥️ Customizable Output:** Choose from various output formats including JSON, simple lists, detailed reports, and more.
- **🗄️ Ephemeral & Permanent Storage:** Option to store downloaded PDFs temporarily (auto-deleted after processing) or permanently.
- **🔐 Custom HTTP Headers:** Add custom headers to HTTP requests for enhanced compatibility and access.
---

## 💻 **Installation**

### 1. **Clone the Repository**

```bash
git clone https://github.com/securezeron/SubPDF.git
cd SubPDF
```

### 2. **Create a Virtual Environment (Recommended)**

```bash
python -m venv venv
```

- **Activate the Virtual Environment:**
  - **Windows:**
    ```bash
    venv\Scripts\activate
    ```
  - **Unix/Linux/MacOS:**
    ```bash
    source venv/bin/activate
    ```

### 3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

> **Note:** Ensure you have Python **3.7** or higher installed.

---

## 🛠️ **Usage**

SubPDF is a **command-line tool**. Below are instructions to help you get started seamlessly.

### 📚 **Basic Commands**

```bash
python main.py [OPTIONS]
```

### 🔧 **Advanced Options**

- **📥 Input Sources:**
  - `-u`, `--url`  
    **Description:** Webpage URL to crawl for PDF links.  
    **Usage:**  
    ```bash
    python main.py -u https://www.example.com
    ```

  - `-pu`, `--pdf-url`  
    **Description:** Direct PDF link to parse.  
    **Usage:**  
    ```bash
    python main.py -pu https://www.example.com/sample.pdf
    ```

  - `-il`, `--input-list`  
    **Description:** A text file containing one URL per line.  
    **Usage:**  
    ```bash
    python main.py -il urls.txt
    ```

  - `-ij`, `--input-json`  
    **Description:** A JSON file containing a list of URLs or a 'urls' array.  
    **Usage:**  
    ```bash
    python main.py -ij urls.json
    ```

- **🗄️ Storage Options:**
  - `-f`, `--download-folder`  
    **Description:** Directory to store downloaded PDFs permanently. If omitted, PDFs are stored temporarily and auto-deleted after processing.  
    **Usage:**  
    ```bash
    python main.py -u https://www.example.com -f /path/to/downloads
    ```

- **🔐 Custom HTTP Headers:**
  - `-H`, `--header`  
    **Description:** Add custom HTTP headers in the format `'HeaderName: Value'`. Can be used multiple times.  
    **Usage:**  
    ```bash
    python main.py -u https://www.example.com -H "Authorization: Bearer YOUR_TOKEN" -H "Custom-Header: Value"
    ```

- **📤 Output Configuration:**
  - `--format`  
    **Description:** Choose the output format.  
    **Options:** `default`, `simple`, `json`, `list`, `domains`  
    **Default:** `default`  
    **Usage:**  
    ```bash
    python main.py -u https://www.example.com --format json
    ```

  - `--output-file`  
    **Description:** Write the final output to a specified file. If omitted, output is printed to stdout.  
    **Usage:**  
    ```bash
    python main.py -u https://www.example.com --output-file results.json
    ```

- **⚙️ Performance:**
  - `-t`, `--threads`  
    **Description:** Number of threads to use for PDF processing.  
    **Default:** `100`  
    **Usage:**  
    ```bash
    python main.py -u https://www.example.com -t 50
    ```

- **🐞 Debugging:**
  - `--debug`  
    **Description:** Enable debug logs for detailed information.  
    **Usage:**  
    ```bash
    python main.py -u https://www.example.com --debug
    ```

### 🔍 **Help Command**

For a comprehensive list of options and their descriptions, use:

```bash
python main.py --help
```

---

## 📈 **Output Formats**

SubPDF offers multiple output formats to cater to different user needs:

1. **Default (`default`):**
   - **Description:** Detailed report listing each PDF and its associated domains and subdomains.
   - **Usage:**  
     ```bash
     python main.py -u https://www.example.com --format default
     ```

2. **Simple (`simple`):**
   - **Description:** Line-by-line list of all extracted domains and subdomains without additional labeling.
   - **Usage:**  
     ```bash
     python main.py -u https://www.example.com --format simple
     ```

3. **JSON (`json`):**
   - **Description:** Structured JSON output mapping each PDF to its domains and subdomains.
   - **Usage:**  
     ```bash
     python main.py -u https://www.example.com --format json --output-file results.json
     ```

4. **List (`list`):**
   - **Description:** Bulleted list format for easy readability.
   - **Usage:**  
     ```bash
     python main.py -u https://www.example.com --format list
     ```

5. **Domains Only (`domains`):**
   - **Description:** Extracted registered domains using `tldextract`, omitting subdomains for a cleaner overview.
   - **Usage:**  
     ```bash
     python main.py -u https://www.example.com --format domains
     ```

---

## 🔥 **Examples**

### 1. **Extract Domains from a Single Webpage**

```bash
python main.py -u https://www.example.com
```

- **Description:** Crawls the specified webpage for PDF links, extracts domains and subdomains from each PDF, and displays the results in the default format.

### 2. **Process Multiple PDFs from a List with Custom Headers**

```bash
python main.py -il urls.txt -H "Authorization: Bearer YOUR_TOKEN" -H "Custom-Header: Value" --output-file domains.json
```

- **Description:** Reads URLs from `urls.txt`, uses custom HTTP headers for requests, extracts domains and subdomains, and saves the results in `domains.json`.

### 3. **Extract Domains in JSON Format with Debug Logs**

```bash
python main.py -pu https://www.example.com/sample.pdf --format json --debug
```

- **Description:** Processes a direct PDF link, outputs the results in JSON format, and provides detailed debug logs for troubleshooting.

### 4. **Limit Processing to 50 Threads and Store PDFs Permanently**

```bash
python main.py -u https://www.example.com -t 50 -f ./downloads
```

- **Description:** Uses up to 50 threads for processing, stores downloaded PDFs in the `./downloads` directory permanently.

---

## 📦 **Dependencies**

SubPDF relies on the following Python libraries:

- **Python 3.7+**
- [Requests](https://pypi.org/project/requests/)
- [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/)
- [PyPDF2](https://pypi.org/project/PyPDF2/)
- [tldextract](https://pypi.org/project/tldextract/)
- [tqdm](https://pypi.org/project/tqdm/)

**Installation via `pip`:**

```bash
pip install -r requirements.txt
```

**Contents of `requirements.txt`:**

```
requests
beautifulsoup4
PyPDF2
tldextract
tqdm
```

---

## 🤝 **Contributing**

Contributions are the heart of SubPDF! Whether it's reporting a bug, suggesting a feature, or submitting a pull request, your input helps make SubPDF better for everyone.

### 1. **Fork the Repository**

Click the **Fork** button at the top right of the repository page.

### 2. **Create a New Branch**

```bash
git checkout -b feature/YourFeatureName
```

### 3. **Make Your Changes**

Implement your feature or fix the bug.

### 4. **Commit Your Changes**

```bash
git commit -m "Add a descriptive message about your changes"
```

### 5. **Push to Your Fork**

```bash
git push origin feature/YourFeatureName
```

### 6. **Create a Pull Request**

Navigate to the original repository and click on **New Pull Request**.

---

## 📝 **License**

Distributed under the [MIT License](LICENSE).

> **Note:** Ensure that you include a `LICENSE` file in your repository with the appropriate license text.

---

## 📞 **Contact**

**Suman Chakraborty**  
Email: [suman@zeron.one](mailto:suman@zeron.one)  
LinkedIn: [linkedin.com/in/suman-chakraborty-b857901b1](https://www.linkedin.com/in/suman-chakraborty-b857901b1)  
GitHub: [github.com/suman-zeron](https://github.com/suman-zeron)

> For any inquiries, issues, or feedback, feel free to reach out!

---

## 🙏 **Acknowledgements**

- [Requests](https://requests.readthedocs.io/en/latest/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [PyPDF2](https://pypi.org/project/PyPDF2/)
- [tldextract](https://pypi.org/project/tldextract/)
- [tqdm](https://tqdm.github.io/)
- [Choose a License](https://choosealicense.com)
- [GitHub Emoji Cheat Sheet](https://www.webpagefx.com/tools/emoji-cheat-sheet/)

---
Made with ❤️ by Suman@ZERON

---
