---
layout: default
title: Dependencies
---

# Dependencies

**Marauder's Mart** leverages a range of external libraries and tools to function effectively. Below is a detailed list of these dependencies, along with links and acknowledgments to their original authors.

## C++ Libraries

### 1. HTTPLib
- **Description:** A single-header C++ HTTP library used for handling HTTP server requests and responses.
- **Source:** [cpp-httplib](https://github.com/yhirose/cpp-httplib)
- **Author:** Yuji Hirose
- **Link:** [httplib.h](https://raw.githubusercontent.com/yhirose/cpp-httplib/refs/heads/master/httplib.h)

### 2. JSON for Modern C++
- **Description:** A single-header library for easy JSON manipulation in C++, providing convenient JSON parsing and serialization.
- **Source:** [nlohmann/json](https://github.com/nlohmann/json)
- **Author:** Niels Lohmann
- **Link:** [json.hpp](https://raw.githubusercontent.com/nlohmann/json/refs/heads/develop/single_include/nlohmann/json.hpp)

### 3. SHA-256 Implementation
- **Description:** A C implementation of the SHA-256 cryptographic hash function, adapted for use in this project as a header.
- **Source:** [crypto-algorithms](https://github.com/B-Con/crypto-algorithms)
- **Author:** Brad Conte
- **Link:** [sha256.h](https://raw.githubusercontent.com/B-Con/crypto-algorithms/refs/heads/master/sha256.c)

## Python Packages

The following Python packages are required to run the front-end and process data:

1. **Streamlit**
   - **Purpose:** Used for developing the web-based user interface.
   - **Installation:** `pip install streamlit`

2. **bcrypt**
   - **Purpose:** Provides secure password hashing for user authentication.
   - **Installation:** `pip install bcrypt`

3. **pathlib**
   - **Purpose:** Used for handling and operating on file system paths in an object-oriented manner.
   - **Installation:** `pip install pathlib`

4. **requests**
   - **Purpose:** Simplified HTTP requests for interacting with the C++ server.
   - **Installation:** `pip install requests`

5. **Pillow**
   - **Purpose:** Python Imaging Library for working with image files.
   - **Installation:** `pip install pillow`

6. **Folium**
   - **Purpose:** Creates interactive leaflet maps, used for visualizing geospatial data.
   - **Installation:** `pip install folium`

7. **NetworkX**
   - **Purpose:** For the creation, manipulation, and study of complex networks (graphs).
   - **Installation:** `pip install networkx`

8. **Streamlit-Folium**
   - **Purpose:** Integration of Folium maps into Streamlit apps.
   - **Installation:** `pip install streamlit-folium`

9. **OSMNX**
   - **Purpose:** For retrieving, constructing, analyzing, and visualizing street networks.
   - **Installation:** `pip install osmnx`

## Additional Tools

- **Clang++ or g++:** Make sure you have a C++ compiler installed to compile the server component.

[Back to Home](index.md)
