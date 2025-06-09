---
layout: default
title: API Endpoints 
---

# API Endpoints

The **Marauder's Mart** backend server provides a set of API endpoints that allow interaction with the blockchain components, handling transactions, and managing escrows. Here’s a detailed look into each endpoint:

## Overview

These endpoints cater to basic financial operations such as deposits and withdrawals, as well as managing escrow transactions for secure trading.

## Available Endpoints

### 1. `/deposit`
- **Method:** `POST`
- **Description:** Deposit GLX currency into a user’s account.
- **Request Body:**
  ```json
  {
      "user": "alice",
      "amount": 50
  }
  ```
- **Response:**
  - Success: `{"status":"ok"}`
  - Failure: `{"status":"fail"}`

### 2. `/withdraw`
- **Method:** `POST`
- **Description:** Withdraw GLX currency from a user’s account.
- **Request Body:**
  ```json
  {
      "user": "alice",
      "amount": 50
  }
  ```
- **Response:**
  - Success: `{"status":"ok"}`
  - Failure: `{"status":"fail"}`

### 3. `/balance`
- **Method:** `GET`
- **Description:** Retrieve a user’s current balance.
- **Query Parameter:**
  - `user=<username>`
- **Response:**
  ```json
  {
      "user": "alice",
      "balance": 100.0
  }
  ```

### 4. `/escrow/open`
- **Method:** `POST`
- **Description:** Open a new escrow transaction.
- **Request Body:**
  ```json
  {
      "buyer": "alice",
      "vendor": "vendorName",
      "product": 100,
      "delivery": 10
  }
  ```
- **Response:**
  - Success: `{"status":"ok", "id": "escrow_id"}`
  - Failure: `{"status":"fail"}`

### 5. `/escrow/release`
- **Method:** `POST`
- **Description:** Release the funds held in an escrow transaction.
- **Request Body:**
  ```json
  {
      "id": "escrow_id"
  }
  ```
- **Response:**
  - Success: `{"status":"ok"}`
  - Failure: `{"status":"fail"}`

### 6. `/chain`
- **Method:** `GET`
- **Description:** Get the current state of the blockchain as a JSON array of blocks.
- **Response:**
  - JSON structure with the chain of blocks.

### 7. `/ledger`
- **Method:** `GET`
- **Description:** Get the current ledger state showing balances.
- **Response:**
  - JSON dictionary of all user balances.

### 8. `/escrows`
- **Method:** `GET`
- **Description:** Get the list of currently open escrows.
- **Response:**
  - JSON array of open escrow details.

## Usage Examples

### Making a Deposit
To deposit 100 GLX to the user "alice", send a POST request to `/deposit` with the body:
json
{
"user": "alice",
"amount": 100
}

### Checking Balance
To check the balance of user "alice", send a GET request to `/balance?user=alice`.

These endpoints provide the critical interactions needed to use Marauder's Mart, facilitating secure and transparent transactions.

For further questions or details, feel free to reach out or consult other documentation sections for more specific information.

[Back to Home](index.md)


---
