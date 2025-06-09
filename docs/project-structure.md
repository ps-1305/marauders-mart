---
layout: default
title: Structure
---

# Project Structure

Understanding the directory structure of the Marauder's Mart project is crucial for effective navigation and contribution. Below is an overview of the project's structure and the purpose of each part.
```
marauders-mart
├── README.md
├── app.py
├── ledger.json
├── LICENSE
├── Makefile
├── marauder_server.cpp
├── pathfinding.py
├── requirements.txt
├── data/
│ └── delhi_vaults.geojson
├── docs/
│ └── index.md
├── inc/
│ ├── httplib.h
│ ├── json.hpp
│ ├── marauder_chain.h
│ └── sha256.h
├── scripts/
│ ├── build_graph.py
│ └── pickup_points.py
```
## Directory and File Overview

- **`README.md`:** Provides a quick overview of the project, setup instructions, and user guidance.
- **`app.py`:** The main script for launching the Streamlit-based front-end, handling user interaction with the blockchain and marketplace.
- **`ledger.json`:** Store for blockchain data, including transactions and escrows; necessary for maintaining state between sessions.
- **`LICENSE`:** Contains licensing information governing the use and distribution of the code.
- **`Makefile`:** Used for compiling the C++ server code. It defines build rules and dependencies for quickly building the binary.
- **`marauder_server.cpp`:** The C++ application serving as the backend server, handling blockchain transactions and HTTP requests.
- **`pathfinding.py`:** Python script for geographical computations and pathfinding, crucial for delivery logistics within the platform.
- **`requirements.txt`:** Lists the Python package dependencies required for the project. Use `pip install -r requirements.txt` to install them.
- **`data/`:** Directory containing data files, such as geographical information relevant to the application.
  - **`delhi_vaults.geojson`:** Example data file with geographical information.
- **`docs/`:** Directory for project documentation, including this documentation setup and any other relevant manuals or guides.
- **`inc/`:** Contains header files used by the C++ server, including third-party and in-house implementations.
  - **`httplib.h`:** A single-header C++ HTTP library used for handling HTTP server functionality.
  - **`json.hpp`:** A library for JSON manipulation in C++, used extensively for handling data serialization.
  - **`marauder_chain.h`:** Implements the blockchain logic specific to Marauder's Mart, including transaction and block management.
  - **`sha256.h`:** Header for SHA-256 hashing, important for ensuring data integrity.
- **`scripts/`:** Contains auxiliary Python scripts used in data processing and preparation.
  - **`build_graph.py`:** Script for constructing graph structures from data.
  - **`pickup_points.py`:** Used for computing or processing pickup points in the platform.

Understanding this structure will help you navigate the Marauder's Mart codebase more effectively, whether you're looking to contribute to development or simply need to understand how the project fits together.

[Back to Home](index.md)
