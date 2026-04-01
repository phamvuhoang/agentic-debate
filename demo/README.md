# Agentic Debate Demo — Setup & Run

This directory contains a self-contained web demo of the `agentic-debate` system.

## Prerequisites

- **Python 3.12+**
- **Node.js & npm** (for building the frontend)
- **Gemini API Key**: You need a valid API key from Google AI Studio.

## Step-by-Step Setup

### 1. Configure the Backend

Navigate to the `demo` directory and install the Python dependencies:

```bash
cd demo
pip install -r requirements.txt
pip install -e ..
```

### 2. Build the Frontend

Vite is used to build the Lit-based frontend assets. These are served as static files by FastAPI.

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Set Environment Variables

Export your Gemini API key:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 4. Run the Application

Start the FastAPI server using `uvicorn`:

```bash
uvicorn backend.main:app --reload
```

The application will be available at [http://localhost:8000](http://localhost:8000).

## 🛠️ Development Mode

For a better development experience with hot-reloading for both backend and frontend:

1.  **Start Backend**: In one terminal, run `uvicorn backend.main:app --reload` in the `demo` directory.
2.  **Start Frontend**: In another terminal, run `npm run dev` in the `demo/frontend` directory.
3.  **Access**: Open [http://localhost:5173](http://localhost:5173). The frontend will proxy `/debate` requests to the backend on port 8000.

> [!NOTE]
> If you get an `Address already in use` error for port 8000, find and kill the process using:
> `lsof -i :8000` then `kill -9 <PID>`

## 🧪 Running Tests

To verify the backend implementation, you can run the test suite:

```bash
cd demo
python -m pytest tests/
```

## Features Demonstrated

- **Dynamic Intent Analysis**: The system reframes your topic and determines the controversy level.
- **Auto-Generated Personas**: Specialized agents are created on-the-fly.
- **Real-Time SSE Streaming**: Experience the debate as it unfolds, powered by A2UI.
- **Adversarial Arbitration**: A final judge evaluates the arguments and provides a verdict.
