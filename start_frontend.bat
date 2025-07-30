@echo off
echo Starting Poker MAM Frontend
echo ==========================
echo.

cd frontend

if not exist "node_modules" (
    echo Installing frontend dependencies...
    echo This may take a few minutes on first run...
    npm install
)

echo.
echo Starting React development server...
echo.
echo Frontend will be available at: http://localhost:3000
echo.

npm start