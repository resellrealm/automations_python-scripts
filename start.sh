#!/bin/bash

echo "Starting Job Swipe App..."
echo ""

# Check if node_modules exist
if [ ! -d "backend/node_modules" ]; then
    echo "Installing backend dependencies..."
    cd backend && npm install && cd ..
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Check if database exists
if [ ! -f "backend/database.sqlite" ]; then
    echo "Seeding database..."
    cd backend && node src/seed.js && cd ..
fi

echo ""
echo "Starting backend server on http://localhost:5000..."
cd backend && npm start &
BACKEND_PID=$!

echo "Starting frontend server on http://localhost:3000..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "Both servers are starting..."
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to press Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
