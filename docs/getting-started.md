---
layout: default
title: Getting Started
---

# Getting Started

Welcome to the setup guide for **Marauder's Mart**. This section will walk you through the process of getting the project up and running on your local machine.

## Prerequisites

Before you begin, ensure you have the following software and tools installed:

- **[Python 3.x](https://www.python.org/downloads/):** Required for running the front-end and data processing scripts.
- **[pip](https://pip.pypa.io/en/stable/installation/):** Package installer for Python, typically included with Python 3.x installations.
- **[Streamlit](https://streamlit.io/):** Used for the interactive user interface.
- **[Clang++ or g++ (C++ Compiler)](https://clang.llvm.org/get_started.html):** Necessary for compiling the C++ server code. Ensure your compiler supports C++17.
- **[SQLite](https://sqlite.org/download.html):** Used for managing the database. Most systems include this by default.

## Installation

1. **Clone the Repository:**
   Open a terminal and run the following command to clone the repository:
   ```sh
   git clone https://github.com/ps-1305/marauders-mart.git
   cd marauders-mart
   ```

2. **Set Up Python Environment:**
   It's a good practice to use a virtual environment for Python projects. Execute:
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Python Dependencies:**
   With the virtual environment activated, install the required packages:
   ```sh
   pip install -r requirements.txt
   ```

4. **Compile the C++ Server:**
   Compile the server component using the provided Makefile:
   ```sh
   make
   ```
   Ensure any necessary environmental variables are set if your compiler isn't in the system PATH.

5. **Initialize the Database:**
   Ensure `users.db` is set up correctly. The application may initialize on its first run, or you might want to provide sample data if necessary.

## Running the Application

1. **Start the C++ Server:**
   Run the compiled server executable:
   ```sh
   ./mm   # On Windows, this might be `mm.exe`
   ```

2. **Launch the Streamlit Application:**
   In a separate terminal, execute:
   ```sh
   streamlit run app.py
   ```

## Additional Configuration

- Make sure to adjust `BASE` in `app.py` if your server runs on a different port or address.
- Follow any comments in the codebase for additional setup requirements or configurations.

You should now have Marauder's Mart running locally. If you encounter any issues during setup, you can correspond with us or raise an issue in the repository.

[Back to Home](index.md)
