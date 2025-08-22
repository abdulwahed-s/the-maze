
import os
import time
import json
import sqlite3
from typing import List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn
HOST = "0.0.0.0"
PORT = 8001
DATABASE_FILE = "leaderboard.db"
def init_database():
    """Initialize SQLite database for leaderboard"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_name_time ON scores (name, time)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")
init_database()
class ScoreIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    time: float = Field(ge=0.0, lt=36000)
app = FastAPI(title="Maze Runner Game", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" />
    <title>Maze Runner</title>
    <style>
        /* Embedded CSS */
        * { box-sizing: border-box; }
        html, body { height: 100%; margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: #0b1020; color: #e9eef7; }
        #app { min-height: 100%; width: 100%; padding: 0; }
        .hidden { display: none !important; }

        .screen { 
            display: none; 
            width: 100%; 
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .screen.active { 
            display: block; 
            opacity: 1;
            transform: translateY(0);
        }
        
        /* Disable animations on mobile for leaderboard to prevent positioning issues */
        @media (max-width: 768px) {
            #leaderboard-screen.active {
                transform: none !important;
                transition: none !important;
                animation: none !important;
            }
            
            /* Also disable base screen animations for leaderboard on mobile */
            #leaderboard-screen {
                transform: none !important;
                transition: none !important;
                animation: none !important;
            }
        }

        /* PC-specific screen overrides */
        @media (hover: hover) and (pointer: fine) {
            .screen { 
                max-width: none !important;
                width: 100vw !important;
                height: 100vh !important;
            }
            .screen.active { 
                display: flex !important; 
            }
        }
        
        /* Ensure interactive elements are clickable on mobile */
        @media (max-width: 768px) {
            #home-screen.active, #game-screen.active {
                z-index: 200 !important;
                position: relative !important;
            }
            
            #home-screen.active .card, #game-screen.active .card {
                z-index: 201 !important;
            }
            
            button, input, label {
                z-index: 202 !important;
                position: relative !important;
            }
        }

        .card { 
            background: #141a2f; 
            border: 1px solid #283150; 
            border-radius: 12px; 
            padding: 24px; 
            margin: 0 auto; 
            width: 100%; 
            max-width: 480px; 
            text-align: center; 
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
            animation: slideIn 0.5s ease-out;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        /* Disable card animations on mobile */
        @media (max-width: 768px) {
            .card {
                animation: none !important;
                transition: none !important;
            }
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(0,0,0,0.4);
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .card h1, .card h2 { margin-top: 0; }

        label { display: block; margin-bottom: 8px; color: #b8c4e0; }
        input { 
            width: 100%; 
            padding: 12px 14px; 
            border-radius: 8px; 
            border: 1px solid #394268; 
            background: #11172a; 
            color: #e9eef7;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        input:focus { 
            outline: none; 
            border-color: #3b82f6; 
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        button { 
            margin-top: 12px; 
            padding: 12px 16px; 
            border-radius: 10px; 
            border: 1px solid #3b82f6; 
            background: #2563eb; 
            color: white; 
            cursor: pointer; 
            font-weight: 600;
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
            transform: translateZ(0);
        }
        button:hover { 
            background: #1d4ed8; 
            transform: translateY(-2px) translateZ(0);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.4);
        }
        
        button[style*="background: #059669"]:hover,
        button[style*="background: #059669"]:hover {
            background: #047857 !important; /* Darker green on hover */
            border-color: #047857 !important;
            box-shadow: 0 8px 20px rgba(4, 120, 87, 0.4) !important;
        }
        button:active { 
            transform: translateY(0) translateZ(0);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        /* Color picker styles */
        .color-option {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 3px solid transparent;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            flex-shrink: 0;
        }

        .color-option:hover {
            transform: scale(1.1);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }

        .color-option.selected {
            border-color: #ffffff;
            box-shadow: 0 0 0 3px #3b82f6, 0 4px 16px rgba(0, 0, 0, 0.4);
            transform: scale(1.15);
        }

        .color-option.selected::after {
            content: '✓';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-weight: bold;
            font-size: 16px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        }

        /* Mobile color picker adjustments */
        @media (max-width: 768px) {
            .color-option {
                width: 36px;
                height: 36px;
            }
            
            .color-option.selected::after {
                font-size: 14px;
            }
        }

        /* Shape picker styles */
        .shape-option {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            border: 3px solid transparent;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .shape-option:hover {
            transform: scale(1.1);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
            border-color: rgba(59, 130, 246, 0.5);
            background: #4b5563;
        }

        .shape-option.selected {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3), 0 4px 16px rgba(0, 0, 0, 0.4);
            transform: scale(1.15);
        }

        .shape-preview {
            width: 24px;
            height: 24px;
            background: #e9eef7;
            border-radius: 2px;
        }

        .shape-preview.circle {
            border-radius: 50%;
        }

        .shape-preview.star {
            background: transparent;
            color: #e9eef7;
            font-size: 20px;
            line-height: 24px;
            text-align: center;
        }

        .shape-preview.diamond {
            transform: rotate(45deg);
        }

        .shape-preview.triangle {
            background: transparent;
            width: 0;
            height: 0;
            border-left: 12px solid transparent;
            border-right: 12px solid transparent;
            border-bottom: 20px solid #e9eef7;
        }

        .shape-preview.square {
            border-radius: 0;
        }

        .shape-preview.rose {
            background: transparent;
            color: #e9eef7;
            font-size: 20px;
            line-height: 24px;
            text-align: center;
        }



        /* Mobile shape picker adjustments */
        @media (max-width: 768px) {
            .shape-option {
                width: 36px;
                height: 36px;
            }
            
            .shape-preview {
                width: 20px;
                height: 20px;
            }
            
            .shape-preview.star {
                font-size: 16px;
                line-height: 20px;
            }
            
            .shape-preview.triangle {
                border-left-width: 10px;
                border-right-width: 10px;
                border-bottom-width: 16px;
            }
            
            .shape-preview.rose {
                font-size: 16px;
                line-height: 20px;
            }

        }

        /* Loading button state */
        button.loading {
            pointer-events: none;
            opacity: 0.7;
        }
        button.loading::after {
            content: '';
            position: absolute;
            width: 16px;
            height: 16px;
            top: 50%;
            left: 50%;
            margin: -8px 0 0 -8px;
            border: 2px solid transparent;
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        #game-screen { width: 100%; }
        .hud { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin: 0 auto 12px; 
            max-width: 640px;
            animation: fadeInDown 0.6s ease-out;
        }
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        #timer { 
            font-size: 24px; 
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            padding: 8px 16px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
            animation: float 3s ease-in-out infinite;
            transition: all 0.3s ease;
        }

        #timer:hover {
            animation: pulse 1s ease-in-out infinite;
            transform: scale(1.1);
        }

        #player-label { 
            font-size: 14px; 
            color: #a3b1d9;
            background: rgba(163, 177, 217, 0.1);
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid rgba(163, 177, 217, 0.2);
            transition: all 0.3s ease;
        }

        #player-label:hover {
            background: rgba(163, 177, 217, 0.2);
            border-color: rgba(163, 177, 217, 0.4);
            transform: scale(1.05);
        }

        #game-canvas { 
            display: block; 
            margin: 0 auto; 
            background: #0f172a; 
            border: 2px solid #334155; 
            border-radius: 8px; 
            width: 100%; 
            height: auto; 
            max-width: 640px;
            animation: zoomIn 0.8s ease-out;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            transition: all 0.3s ease;
        }

        #game-canvas:hover {
            border-color: #3b82f6;
            box-shadow: 0 12px 40px rgba(59, 130, 246, 0.3);
        }
        @keyframes zoomIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }

        .controls { 
            display: grid; 
            place-items: center; 
            margin-top: 16px;
            animation: fadeInUp 0.6s ease-out 0.2s both;
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .dpad { display: grid; grid-template-rows: auto auto; gap: 12px; align-items: center; }
        .dpad .top-row { display: flex; justify-content: center; }
        .dpad .bottom-row { display: flex; justify-content: center; gap: 12px; }
        .dpad button { 
            width: 64px; 
            height: 64px; 
            border-radius: 12px; 
            font-size: 24px; 
            background: linear-gradient(135deg, #1e293b, #334155);
            border: 1px solid #475569;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .dpad button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.5s ease;
        }

        .dpad button:hover::before {
            left: 100%;
        }

        .dpad button:hover {
            background: linear-gradient(135deg, #334155, #475569);
            transform: scale(1.1) rotate(2deg);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
            border-color: #3b82f6;
        }

        .dpad button:active {
            transform: scale(0.95);
            transition: transform 0.1s ease;
        }

        .overlay { 
            position: fixed; 
            inset: 0; 
            display: grid; 
            place-items: center; 
            background: rgba(0,0,0,0.7);
            opacity: 0;
            visibility: hidden;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(4px);
        }
        .overlay.active { 
            opacity: 1;
            visibility: visible;
        }
        .overlay.hidden { 
            opacity: 0;
            visibility: hidden;
        }

        .modal { 
            background: linear-gradient(135deg, #0b1224, #141a2f);
            border: 1px solid #2b345a; 
            padding: 24px; 
            border-radius: 12px; 
            width: 90%; 
            max-width: 420px; 
            text-align: center;
            transform: scale(0.9) translateY(20px);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        .overlay.active .modal {
            transform: scale(1) translateY(0);
        }

        .modal-actions { display: flex; gap: 12px; justify-content: center; margin-top: 16px; }

        .table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 12px;
            animation: fadeIn 0.6s ease-out 0.3s both;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .table th, .table td { 
            border-bottom: 1px solid #233152; 
            padding: 10px; 
            text-align: left;
            transition: background-color 0.2s ease;
        }
        .table th { color: #9fb4dd; font-weight: 600; }
        .table tbody tr {
            transition: all 0.3s ease;
            transform: translateX(0);
        }

        .table tbody tr:hover {
            background: rgba(59, 130, 246, 0.15);
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
        }

        /* Loading spinner */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
            margin-right: 8px;
        }

        /* Progress bar */
        .progress-container {
            width: 100%;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 3px;
            margin: 16px 0;
            overflow: hidden;
            position: relative;
        }

        .progress-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .progress-bar {
            height: 6px;
            background: linear-gradient(90deg, #3b82f6, #1d4ed8, #3b82f6);
            background-size: 200% 100%;
            border-radius: 8px;
            width: 0%;
            transition: width 0.3s ease;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
            animation: gradientMove 3s ease infinite;
        }

        @keyframes gradientMove {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Enhanced visual effects */
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
        }

        /* Critical fix for leaderboard positioning on all devices - top of screen on mobile */
        #leaderboard-screen.active {
            position: relative !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            margin: 0 !important;
            transform: none !important;
            display: flex !important;
            align-items: flex-start !important;
            justify-content: center !important;
            min-height: 100vh !important;
            width: 100% !important;
            box-sizing: border-box !important;
            padding-top: 16px !important;
        }
        
        /* Force mobile leaderboard to stay at top - highest priority */
        @media (max-width: 768px) {
            #leaderboard-screen.active {
                align-items: flex-start !important;
                justify-content: flex-start !important;
                padding-top: 16px !important;
            }
            
            /* Ensure the card itself doesn't get centered */
            #leaderboard-screen.active .card {
                align-self: flex-start !important;
                margin-top: 0 !important;
            }
        }
        
        /* Force mobile leaderboard to stay at top and visible */
        @media (max-width: 768px) {
            #leaderboard-screen.active {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
                transform: none !important;
                transition: none !important;
                z-index: 100 !important;
            }
        }

        #leaderboard-screen.active .card {
            position: relative !important;
            top: auto !important;
            left: auto !important;
            right: auto !important;
            bottom: auto !important;
            transform: none !important;
            margin: 0 auto !important;
            max-height: 85vh !important;
            height: auto !important;
            display: flex !important;
            flex-direction: column !important;
        }
        
        /* Ensure mobile leaderboard card stays visible and properly positioned */
        @media (max-width: 768px) {
            #leaderboard-screen.active .card {
                position: relative !important;
                top: auto !important;
                left: auto !important;
                right: auto !important;
                bottom: auto !important;
                transform: none !important;
                transition: none !important;
                animation: none !important;
                margin: 0 auto !important;
                max-height: 85vh !important;
                height: auto !important;
                display: flex !important;
                flex-direction: column !important;
                width: 100% !important;
                max-width: 95vw !important;
                align-self: flex-start !important;
            }
        }

        /* Maze generation animation */
        .maze-building {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(11, 16, 32, 0.95);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10;
            border-radius: 8px;
        }

        .maze-building.hidden {
            display: none;
        }

        .maze-building::before {
            content: 'Building maze...';
            color: #3b82f6;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            text-align: center;
        }

        #canvas-container {
            position: relative;
            display: inline-block;
            margin: 0 auto;
        }

        #maze-building-overlay .progress-container {
            width: 200px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 4px;
            overflow: hidden;
        }

        #maze-building-overlay .progress-bar {
            height: 8px;
            background: linear-gradient(90deg, #3b82f6, #1d4ed8);
            border-radius: 6px;
            width: 0%;
            transition: width 0.2s ease;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }

        .table-scroll {
            max-height: 50vh;
            overflow-y: auto;
            overflow-x: hidden;
            margin-top: 12px;
            border: 1px solid #233152;
            border-radius: 8px;
            background: rgba(20, 26, 47, 0.8);
        }
        
        /* Mobile table scroll adjustments */
        @media (max-width: 768px) {
            .table-scroll {
                max-height: none !important;
                flex: 1 !important;
                min-height: 200px !important;
            }
        }

        /* Custom scrollbar for table container */
        .table-scroll::-webkit-scrollbar {
            width: 8px;
        }

        .table-scroll::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }

        .table-scroll::-webkit-scrollbar-thumb {
            background: rgba(59, 130, 246, 0.6);
            border-radius: 4px;
        }

        .table-scroll::-webkit-scrollbar-thumb:hover {
            background: rgba(59, 130, 246, 0.8);
        }

        #leaderboard-loading { 
            align-self: center; 
            margin: 16px 0;
        }

        /* Show on-screen controls only on touch/mobile devices */
        .controls { display: none; }
        
        /* JavaScript fallback for mobile detection */
        .mobile-device .controls { display: grid !important; }
        
        .mobile-device #game-screen {
            display: flex !important;
            flex-direction: column !important;
            min-height: 100vh !important;
            padding: 0 !important;
        }
        
        .mobile-device .hud { 
            position: absolute !important;
            top: 12px !important;
            left: 12px !important;
            right: 12px !important;
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            margin: 0 !important;
            max-width: none !important;
            z-index: 10 !important;
        }
        
        .mobile-device #canvas-container {
            flex: 1 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 60px 12px 12px 12px !important;
        }
        
        .mobile-device #timer { order: 1 !important; }
        .mobile-device #player-label { order: 2 !important; }
        
        /* Mobile leaderboard fixes */
        .mobile-device #leaderboard-screen {
            padding: 8px !important;
            display: flex !important;
            align-items: flex-start !important;
            justify-content: center !important;
            min-height: 100vh !important;
            width: 100% !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            transform: none !important;
            transition: none !important;
            animation: none !important;
            z-index: 100 !important;
        }
        
        .mobile-device #leaderboard-screen .card {
            max-height: 90vh !important;
            height: auto !important;
            display: flex !important;
            flex-direction: column !important;
            margin: 0 !important;
            padding: 16px !important;
            width: 100% !important;
            max-width: 95vw !important;
        }
        
        .mobile-device #leaderboard-screen .card h2 {
            margin-top: 0 !important;
            margin-bottom: 12px !important;
            font-size: 20px !important;
            flex-shrink: 0 !important;
        }
        
        .mobile-device .table-scroll {
            flex: 1 !important;
            max-height: none !important;
            margin-top: 8px !important;
            margin-bottom: 8px !important;
            min-height: 200px !important;
        }
        
        .mobile-device #play-again-btn {
            margin-top: 8px !important;
            flex-shrink: 0 !important;
        }
        
        .mobile-device #leaderboard-loading {
            margin: 8px 0 !important;
        }
        
        /* Force mobile leaderboard centering with highest priority */
        @media (max-width: 768px) {
            /* Prevent body scroll on mobile */
            html, body {
                height: 100vh !important;
                overflow: hidden !important;
                position: fixed !important;
                width: 100% !important;
            }
            
            #app {
                height: 100vh !important;
                overflow: hidden !important;
            }
            
            #leaderboard-screen.active {
                display: flex !important;
                align-items: flex-start !important;
                justify-content: flex-start !important;
                height: 100vh !important;
                width: 100% !important;
                padding: 16px 8px 8px 8px !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
                margin: 0 !important;
                transform: none !important;
                transition: none !important;
                z-index: 100 !important;
            }
            
            #leaderboard-screen.active .card {
                max-height: 85vh !important;
                height: auto !important;
                margin: 0 !important;
                position: relative !important;
                top: auto !important;
                left: auto !important;
                right: auto !important;
                bottom: auto !important;
                transform: none !important;
                transition: none !important;
                animation: none !important;
                display: flex !important;
                flex-direction: column !important;
                width: 100% !important;
                max-width: 95vw !important;
            }
        }
        
        /* Mobile device detection - multiple approaches for better compatibility */
        @media (hover: none) and (pointer: coarse), 
               (max-width: 768px), 
               (pointer: coarse), 
               (max-width: 1024px) and (orientation: portrait) {
            /* Prevent body scroll on mobile */
            html, body {
                height: 100vh !important;
                overflow: hidden !important;
                position: fixed !important;
                width: 100% !important;
            }
            
            #app {
                height: 100vh !important;
                overflow: hidden !important;
            }
            
            .controls { 
                display: grid; 
                z-index: 200;
                position: relative;
            }
            
            /* Mobile game screen layout */
            #game-screen {
                display: flex !important;
                flex-direction: column !important;
                height: 100vh !important;
                padding: 0 !important;
                overflow: hidden !important;
            }
            
            /* Mobile HUD positioning */
            .hud { 
                position: absolute;
                top: 12px;
                left: 12px;
                right: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 0;
                max-width: none;
                z-index: 200;
            }
            
            /* Canvas container for mobile */
            #canvas-container {
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 60px 12px 12px 12px; /* top padding for HUD */
            }
            
            /* Ensure timer left and player name right on mobile */
            #timer { order: 1; }
            #player-label { order: 2; }
            
            /* Mobile leaderboard fixes - POSITIONED AT TOP */
            #leaderboard-screen {
                display: flex !important;
                align-items: flex-start !important;
                justify-content: center !important;
                height: 100vh !important;
                width: 100% !important;
                padding: 16px 8px 8px 8px !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
                margin: 0 !important;
                transform: none !important;
                transition: none !important;
                z-index: 100 !important;
            }
            
            #leaderboard-screen .card {
                max-height: 85vh !important;
                height: auto !important;
                display: flex !important;
                flex-direction: column !important;
                margin: 0 !important;
                padding: 20px !important;
                width: 100% !important;
                max-width: 95vw !important;
                position: relative !important;
                top: auto !important;
                left: auto !important;
                right: auto !important;
                bottom: auto !important;
                transform: none !important;
            }
            
            #leaderboard-screen .card h2 {
                margin-top: 0 !important;
                margin-bottom: 16px !important;
                font-size: 22px !important;
                flex-shrink: 0 !important;
            }
            
            .table-scroll {
                flex: 1 !important;
                max-height: none !important;
                margin: 12px 0 !important;
                min-height: 200px !important;
            }
            
            #play-again-btn {
                margin-top: 16px !important;
                flex-shrink: 0 !important;
            }
            
            #leaderboard-loading {
                margin: 12px 0 !important;
            }
        }

        @media (hover: hover) and (pointer: fine) {
            /* Desktop: use full viewport and prevent scroll while playing */
            html, body { height: 100%; overflow: hidden; }
            #app { width: 100vw; height: 100vh; }

            /* Game screen specific layout for desktop */
            #game-screen.active { 
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                overflow: hidden; /* avoid scroll while playing */
            }
            
            .hud { 
                position: absolute; 
                top: 20px; 
                left: 20px; 
                right: 20px; 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                margin: 0; 
                max-width: none; 
                pointer-events: none; /* let clicks pass through */
                z-index: 10;
            }
            
            #canvas-container { 
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
            }
            
            #timer, #player-label { pointer-events: auto; }

            /* Ensure name left and timer right in HUD */
            #player-label { order: 1; }
            #timer { order: 2; margin-left: auto; }

            /* Center all main screens properly on PC */
            #home-screen.active, #leaderboard-screen.active, #loading-screen.active {
                align-items: center !important;
                justify-content: center !important;
                height: 100vh !important;
                width: 100vw !important;
                padding: 20px !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
                box-sizing: border-box !important;
                margin: 0 !important;
            }

            /* Ensure cards are properly sized on PC */
            #home-screen .card, #loading-screen .card {
                max-width: 500px !important;
                width: 100% !important;
                margin: 0 auto !important;
                flex-shrink: 0 !important;
            }
            
            #leaderboard-screen .card {
                max-width: 800px !important;
                width: 100% !important;
                max-height: 90vh !important;
                margin: 0 auto !important;
                flex-shrink: 0 !important;
                overflow-x: hidden !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: stretch !important;
                overflow: hidden !important;
            }
        }

        @media (min-width: 720px) {
            .dpad button { width: 72px; height: 72px; font-size: 28px; }
        } 

        /* Fallback centering for mobile and general cases */
        @media not all and (hover: hover) and (pointer: fine) {
            /* Prevent body scroll on mobile */
            html, body {
                height: 100vh !important;
                overflow: hidden !important;
                position: fixed !important;
                width: 100% !important;
            }
            
            #app {
                height: 100vh !important;
                overflow: hidden !important;
            }
            
            #home-screen.active, #loading-screen.active {
                display: grid !important;
                place-items: center !important;
                height: 100vh !important;
                width: 100% !important;
                padding: 16px !important;
                overflow: hidden !important;
            }

            #game-screen.active {
                display: grid !important;
                place-items: center !important;
                height: 100vh !important;
                width: 100% !important;
                overflow: hidden !important;
            }

            /* Special handling for leaderboard to ensure proper mobile positioning at top */
            #leaderboard-screen.active {
                display: flex !important;
                align-items: flex-start !important;
                justify-content: flex-start !important;
                height: 100vh !important;
                width: 100% !important;
                padding: 16px 8px 8px 8px !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
                margin: 0 !important;
                transform: none !important;
                transition: none !important;
                z-index: 100 !important;
            }

            #leaderboard-screen .card {
                max-height: 85vh;
                height: auto;
                display: flex;
                flex-direction: column;
                align-items: stretch;
                overflow: hidden;
                position: relative !important;
                top: auto !important;
                left: auto !important;
                right: auto !important;
                bottom: auto !important;
                transform: none !important;
                transition: none !important;
                animation: none !important;
                width: 100% !important;
                max-width: 95vw !important;
            }
        }
    </style>
</head>

<body>
    <div id="app">
        <!-- Loading Screen -->
        <section id="loading-screen" class="screen active">
            <div class="card">
                <h1>Maze Runner</h1>
                <div class="progress-container">
                    <div class="progress-bar" id="loading-progress"></div>
                </div>
                <p>Loading game...</p>
            </div>
        </section>

        <!-- Home Screen -->
        <section id="home-screen" class="screen">
            <div class="card">
                <h1>Maze Runner</h1>
                <label for="player-name">Enter your name</label>
                <input id="player-name" type="text" placeholder="Player" />
                
                <label for="player-color" style="margin-top: 16px;">Choose your color</label>
                <div style="display: flex; gap: 8px; margin-top: 8px; justify-content: center; flex-wrap: wrap;">
                    <div class="color-option" data-color="#22c55e" style="background: #22c55e;"></div>
                    <div class="color-option" data-color="#3b82f6" style="background: #3b82f6;"></div>
                    <div class="color-option" data-color="#f97316" style="background: #f97316;"></div>
                    <div class="color-option" data-color="#8b5cf6" style="background: #8b5cf6;"></div>
                    <div class="color-option" data-color="#ec4899" style="background: #ec4899;"></div>
                    <div class="color-option" data-color="#f59e0b" style="background: #f59e0b;"></div>
                    <div class="color-option" data-color="#10b981" style="background: #10b981;"></div>
                    <div class="color-option" data-color="#ef4444" style="background: #ef4444;"></div>
                    </div>
                    
                <label for="player-shape" style="margin-top: 16px;">Choose your shape</label>
                <div style="display: flex; gap: 8px; margin-top: 8px; justify-content: center; flex-wrap: wrap;">
                    <div class="shape-option" data-shape="circle" style="background: #374151;">
                        <div class="shape-preview circle"></div>
                        </div>
                    <div class="shape-option" data-shape="star" style="background: #374151;">
                        <div class="shape-preview star">★</div>
                    </div>
                    <div class="shape-option" data-shape="diamond" style="background: #374151;">
                        <div class="shape-preview diamond"></div>
                    </div>
                    <div class="shape-option" data-shape="triangle" style="background: #374151;">
                        <div class="shape-preview triangle"></div>
                        </div>
                    <div class="shape-option" data-shape="square" style="background: #374151;">
                        <div class="shape-preview square"></div>
                    </div>
                    <div class="shape-option" data-shape="rose" style="background: #374151;">
                        <div class="shape-preview rose">✿</div>
                    </div>
                    
                </div>
                
                <div style="display: flex; gap: 12px; margin-top: 16px;">
                    <button id="start-btn" style="flex: 1;">Start Game</button>
                    <button id="home-leaderboard-btn" style="flex: 1; background: #059669; border-color: #059669;">View Leaderboard</button>
                </div>
            </div>
        </section>

        <!-- Game Screen -->
        <section id="game-screen" class="screen">
            <div class="hud">
                <div id="timer">00.00</div>
                <div id="player-label"></div>
            </div>
            
            <div id="canvas-container">
                <canvas id="game-canvas" width="640" height="640"></canvas>
                <div id="maze-building-overlay" class="maze-building hidden">
                    <div class="progress-container">
                        <div class="progress-bar" id="maze-progress"></div>
                    </div>
                </div>
            </div>
            
            <div class="controls">
                <div class="dpad">
                    <div class="top-row">
                        <button id="btn-up" aria-label="Up">▲</button>
                    </div>
                    <div class="bottom-row">
                        <button id="btn-left" aria-label="Left">◀</button>
                        <button id="btn-down" aria-label="Down">▼</button>
                        <button id="btn-right" aria-label="Right">▶</button>
                    </div>
                </div>
            </div>

            <!-- Win Overlay -->
            <div id="win-overlay" class="overlay hidden">
                <div class="modal">
                    <h2>🎉 You finished the maze!</h2>
                    <p id="final-time">Time: 0.00s</p>
                    <div class="modal-actions">
                        <button id="view-leaderboard-btn">View Leaderboard</button>
                        <button id="try-again-btn">Try Again</button>
                    </div>
                </div>
            </div>
        </section>

        <!-- Leaderboard Screen -->
        <section id="leaderboard-screen" class="screen">
            <div class="card">
                <h2>Leaderboard</h2>
                <div id="leaderboard-loading" class="hidden">
                    <span class="loading-spinner"></span> Loading scores...
                </div>
                <div class="table-scroll">
                <table class="table" id="leaderboard-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Player</th>
                            <th>Best Time (s)</th>
                        </tr>
                    </thead>
                    <tbody id="leaderboard-body"></tbody>
                </table>
                </div>
                <button id="play-again-btn">Play Again</button>
            </div>
        </section>
    </div>

    <!-- Pyodide loader with fallback -->
    <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
    <script>
        // Force show controls on mobile devices - JavaScript fallback
        function detectMobile() {
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
                           ('ontouchstart' in window) ||
                           (navigator.maxTouchPoints > 0) ||
                           (window.innerWidth <= 768);
            
            if (isMobile) {
                document.documentElement.style.setProperty('--force-mobile-controls', 'grid');
                document.body.classList.add('mobile-device');
            }
        }
        
        // Color picker functionality
        function initializeColorPicker() {
            const colorOptions = document.querySelectorAll('.color-option');
            const defaultColor = '#22c55e';
            
            // Set default color as selected
            document.querySelector(`[data-color="${defaultColor}"]`).classList.add('selected');
            
            colorOptions.forEach(option => {
                option.addEventListener('click', function() {
                    // Remove selection from all options
                    colorOptions.forEach(opt => opt.classList.remove('selected'));
                    // Add selection to clicked option
                    this.classList.add('selected');
                    
                    // Update the color preview in the player name input if it has a value
                    const nameInput = document.getElementById('player-name');
                    if (nameInput && nameInput.value.trim()) {
                        updatePlayerPreview();
                    }
                });
            });
        }
        
        // Shape picker functionality
        function initializeShapePicker() {
            const shapeOptions = document.querySelectorAll('.shape-option');
            const defaultShape = 'circle';
            
            // Set default shape as selected
            document.querySelector(`[data-shape="${defaultShape}"]`).classList.add('selected');
            
            shapeOptions.forEach(option => {
                option.addEventListener('click', function() {
                    // Remove selection from all options
                    shapeOptions.forEach(opt => opt.classList.remove('selected'));
                    // Add selection to clicked option
                    this.classList.add('selected');
                    
                    // Update the player preview if name input has a value
                    const nameInput = document.getElementById('player-name');
                    if (nameInput && nameInput.value.trim()) {
                        updatePlayerPreview();
                    }
                });
            });
        }
        
        // Update player preview with selected color and shape
        function updatePlayerPreview() {
            const nameInput = document.getElementById('player-name');
            const selectedColor = getSelectedColor();
            const selectedShape = getSelectedShape();
            const playerName = nameInput.value.trim() || 'Player';
            
            // Add a small preview next to the input
            let previewElement = document.getElementById('player-preview');
            if (!previewElement) {
                previewElement = document.createElement('div');
                previewElement.id = 'player-preview';
                previewElement.style.cssText = 'margin-top: 8px; font-size: 14px; color: #94a3b8; text-align: center;';
                nameInput.parentNode.insertBefore(previewElement, nameInput.nextSibling);
            }
            
            // Create shape symbol based on selection
            let shapeSymbol = '●'; // default circle
            if (selectedShape === 'star') shapeSymbol = '★';
            else if (selectedShape === 'diamond') shapeSymbol = '◆';
            else if (selectedShape === 'triangle') shapeSymbol = '▲';
            else if (selectedShape === 'square') shapeSymbol = '■';
            else if (selectedShape === 'rose') shapeSymbol = '✿';
            
            previewElement.innerHTML = `<span style="color: ${selectedColor};">${shapeSymbol}</span> ${playerName}`;
        }
        
        // Get selected color
        function getSelectedColor() {
            const selectedOption = document.querySelector('.color-option.selected');
            return selectedOption ? selectedOption.dataset.color : '#22c55e';
        }
        
        // Get selected shape
        function getSelectedShape() {
            const selectedOption = document.querySelector('.shape-option.selected');
            return selectedOption ? selectedOption.dataset.shape : 'circle';
        }
        
        // Run mobile detection
        detectMobile();
        
        // Initialize color picker
        initializeColorPicker();
        
        // Initialize shape picker
        initializeShapePicker();
        
        // Add name input listener for live preview
        const nameInput = document.getElementById('player-name');
        if (nameInput) {
            nameInput.addEventListener('input', updatePlayerPreview);
        }
        
        // Re-run on resize
        window.addEventListener('resize', detectMobile);
    </script>
    <script>
        // Embedded Python game code
        const PYTHON_GAME_CODE = `
# pyright: reportMissingImports=false
from js import document, window, JSON
from math import floor
import random
import time
import json
from pyodide.ffi import create_proxy, to_js

# ------------------------------ Config ------------------------------
GRID_SIZE = 20               # cells per side
CELL_PIXELS = 32             # canvas pixels per cell (640px canvas)
WALL_THICKNESS = 2
DEFAULT_PLAYER_COLOR = "#22c55e"  # Default color, can be changed
PATH_COLOR = "#0f172a"
WALL_COLOR = "#334155"
START_POS = (0, 0)
EXIT_POS = (GRID_SIZE - 1, GRID_SIZE - 1)
# Toggle for animated vs instant maze generation
USE_ANIMATED_BUILD = False

# Backend API base - use current host and port for standalone version
def _compute_api_base_url() -> str:
    return f"{window.location.protocol}//{window.location.host}/api"

API_BASE_URL = _compute_api_base_url()

# ------------------------------ State ------------------------------
class GameState:
    def __init__(self) -> None:
        self.player_name: str = ""
        self.player_color: str = DEFAULT_PLAYER_COLOR  # Player's chosen color
        self.player_shape: str = "circle"  # Player's chosen shape
        self.grid_width: int = GRID_SIZE
        self.grid_height: int = GRID_SIZE
        self.maze_walls = None  # dict with walls per cell
        self.player_cell = list(START_POS)
        self.start_time_s: float | None = None
        self.finished: bool = False
        self.final_time_s: float = 0.0
        self.submitted: bool = False
        self.maze_generating: bool = False

state = GameState()

canvas = document.getElementById("game-canvas")
ctx = canvas.getContext("2d") if canvas else None

timer_el = document.getElementById("timer")
player_label_el = document.getElementById("player-label")
win_overlay_el = document.getElementById("win-overlay")
final_time_el = document.getElementById("final-time")
leaderboard_body_el = document.getElementById("leaderboard-body")
leaderboard_loading_el = document.getElementById("leaderboard-loading")
leaderboard_table_el = document.getElementById("leaderboard-table")
maze_building_overlay = document.getElementById("maze-building-overlay")
maze_progress_bar = document.getElementById("maze-progress")

# Screens
loading_screen = document.getElementById("loading-screen")
home_screen = document.getElementById("home-screen")
game_screen = document.getElementById("game-screen")
leaderboard_screen = document.getElementById("leaderboard-screen")

# Buttons
start_btn = document.getElementById("start-btn")
home_leaderboard_btn = document.getElementById("home-leaderboard-btn")
play_again_btn = document.getElementById("play-again-btn")
view_leaderboard_btn = document.getElementById("view-leaderboard-btn")
try_again_btn = document.getElementById("try-again-btn")

btn_up = document.getElementById("btn-up")
btn_down = document.getElementById("btn-down")
btn_left = document.getElementById("btn-left")
btn_right = document.getElementById("btn-right")

# Keep proxies to prevent garbage collection
_event_proxies = {}

# ------------------------------ Utility ------------------------------

def show_screen(screen_id: str) -> None:
    # Smooth transition between screens
    for s in [loading_screen, home_screen, game_screen, leaderboard_screen]:
        if s and s.id == screen_id:
            s.classList.add("active")
        elif s:
            s.classList.remove("active")


def set_overlay_visible(visible: bool) -> None:
    if visible:
        win_overlay_el.classList.remove("hidden")
        win_overlay_el.classList.add("active")
    else:
        win_overlay_el.classList.remove("active")
        win_overlay_el.classList.add("hidden")


def format_time_s(seconds: float) -> str:
    return f"{seconds:.2f}"





def show_loading_state(button, loading: bool = True):
    # Show/hide loading state on buttons
    if loading:
        button.classList.add("loading")
        button.disabled = True
    else:
        button.classList.remove("loading")
        button.disabled = False


# ------------------------------ Maze Generation ------------------------------
# Maze represented with walls for each cell: dict keyed by (x,y) -> {N,S,E,W: bool}
# True means wall exists

async def generate_maze_animated(width: int, height: int) -> dict:
    # Generate maze with visual animation
    state.maze_generating = True
    
    # Show maze building overlay
    maze_building_overlay.classList.remove("hidden")
    
    # Initialize all walls
    walls = {}
    for y in range(height):
        for x in range(width):
            walls[(x, y)] = {'N': True, 'S': True, 'E': True, 'W': True}
    
    visited = set()
    stack = [(0, 0)]
    visited.add((0, 0))
    
    opposite = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
    total_cells = width * height
    processed_cells = 1
    
    # Draw initial state
    draw_maze(walls)
    
    # Animation frame counter for smooth updates
    frame_count = 0
    update_frequency = 3  # Update every 3 frames for smooth animation
    
    while stack:
        cx, cy = stack[-1]
        unvisited_neighbors = []
        for dx, dy, direction in [(0,-1,'N'), (0,1,'S'), (1,0,'E'), (-1,0,'W')]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in visited:
                    unvisited_neighbors.append((nx, ny, direction))

        if unvisited_neighbors:
            nx, ny, direction = random.choice(unvisited_neighbors)
            # carve wall
            walls[(cx, cy)][direction] = False
            walls[(nx, ny)][opposite[direction]] = False
            visited.add((nx, ny))
            stack.append((nx, ny))
            
            # Update progress and redraw
            processed_cells += 1
            progress = (processed_cells / total_cells) * 100
            maze_progress_bar.style.width = f"{progress}%"
            
            # Only redraw every few frames for smooth animation
            frame_count += 1
            if frame_count % update_frequency == 0:
                draw_maze(walls)
                
                # Use JavaScript Promise for smooth delay
                await window.pyodide.runPythonAsync("import asyncio; await asyncio.sleep(0.03)")
        else:
            stack.pop()
    
    # Final render to ensure complete maze
    draw_maze(walls)
    
    # Hide overlay and finish
    maze_building_overlay.classList.add("hidden")
    state.maze_generating = False
    return walls


def generate_maze(width: int, height: int) -> dict:
    # Synchronous maze generation (fallback)
    def neighbors(cx: int, cy: int):
        for dx, dy, direction in [(0,-1,'N'), (0,1,'S'), (1,0,'E'), (-1,0,'W')]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny, direction

    # Initialize all walls
    walls = {}
    for y in range(height):
        for x in range(width):
            walls[(x, y)] = {'N': True, 'S': True, 'E': True, 'W': True}

    visited = set()
    stack = [(0, 0)]
    visited.add((0, 0))

    opposite = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}

    while stack:
        cx, cy = stack[-1]
        unvisited_neighbors = []
        for nx, ny, direction in neighbors(cx, cy):
            if (nx, ny) not in visited:
                unvisited_neighbors.append((nx, ny, direction))

        if unvisited_neighbors:
            nx, ny, direction = random.choice(unvisited_neighbors)
            # carve wall
            walls[(cx, cy)][direction] = False
            walls[(nx, ny)][opposite[direction]] = False
            visited.add((nx, ny))
            stack.append((nx, ny))
        else:
            stack.pop()

    return walls

# ------------------------------ Rendering ------------------------------

def clear_canvas() -> None:
    if not ctx:
        return
    ctx.fillStyle = PATH_COLOR
    ctx.fillRect(0, 0, canvas.width, canvas.height)


def draw_maze(walls: dict) -> None:
    clear_canvas()
    if not ctx:
        return
    ctx.strokeStyle = WALL_COLOR
    ctx.lineWidth = WALL_THICKNESS
    
    # Draw walls with smooth animation effect
    for (x, y), w in walls.items():
        px = x * CELL_PIXELS
        py = y * CELL_PIXELS
        if w['N']:
            ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px + CELL_PIXELS, py); ctx.stroke()
        if w['S']:
            ctx.beginPath(); ctx.moveTo(px, py + CELL_PIXELS); ctx.lineTo(px + CELL_PIXELS, py + CELL_PIXELS); ctx.stroke()
        if w['W']:
            ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px, py + CELL_PIXELS); ctx.stroke()
        if w['E']:
            ctx.beginPath(); ctx.moveTo(px + CELL_PIXELS, py); ctx.lineTo(px + CELL_PIXELS, py + CELL_PIXELS); ctx.stroke()

    # draw start & exit with glow effect
    ctx.shadowColor = "#0ea5e9"
    ctx.shadowBlur = 10
    ctx.fillStyle = "#0ea5e9"
    rectpad = 6
    sx, sy = START_POS
    ex, ey = EXIT_POS
    ctx.fillRect(sx * CELL_PIXELS + rectpad, sy * CELL_PIXELS + rectpad, CELL_PIXELS - 2*rectpad, CELL_PIXELS - 2*rectpad)
    
    ctx.shadowColor = "#f97316"
    ctx.fillStyle = "#f97316"
    ctx.fillRect(ex * CELL_PIXELS + rectpad, ey * CELL_PIXELS + rectpad, CELL_PIXELS - 2*rectpad, CELL_PIXELS - 2*rectpad)
    
    # Reset shadow
    ctx.shadowBlur = 0


def draw_player(cell_x: int, cell_y: int) -> None:
    if not ctx:
        return
    
    px = cell_x * CELL_PIXELS
    py = cell_y * CELL_PIXELS
    pad = 8
    size = CELL_PIXELS - 2*pad
    center_x = px + CELL_PIXELS // 2
    center_y = py + CELL_PIXELS // 2
    
    # Add glow effect to player using selected color
    ctx.shadowColor = state.player_color
    ctx.shadowBlur = 15
    ctx.fillStyle = state.player_color
    
    # Draw different shapes based on player selection
    if state.player_shape == "circle":
        ctx.beginPath()
        ctx.arc(center_x, center_y, size // 2, 0, 2 * 3.14159)
        ctx.fill()
    
    elif state.player_shape == "star":
        # Draw a star using multiple triangles
        ctx.save()
        ctx.translate(center_x, center_y)
        ctx.rotate(3.14159 / 2)  # Rotate 90 degrees
        
        # Draw 5-pointed star
        for i in range(5):
            ctx.rotate(2 * 3.14159 / 5)
            ctx.beginPath()
            ctx.moveTo(0, -size // 2)
            ctx.lineTo(size // 8, -size // 4)
            ctx.lineTo(size // 2, -size // 4)
            ctx.lineTo(size // 4, 0)
            ctx.lineTo(size // 2, size // 4)
            ctx.lineTo(size // 8, size // 4)
            ctx.closePath()
            ctx.fill()
        ctx.restore()
    
    elif state.player_shape == "diamond":
        ctx.beginPath()
        ctx.moveTo(center_x, py + pad)
        ctx.lineTo(px + CELL_PIXELS - pad, center_y)
        ctx.lineTo(center_x, py + CELL_PIXELS - pad)
        ctx.lineTo(px + pad, center_y)
        ctx.closePath()
        ctx.fill()
    
    elif state.player_shape == "triangle":
        ctx.beginPath()
        ctx.moveTo(center_x, py + pad)
        ctx.lineTo(px + pad, py + CELL_PIXELS - pad)
        ctx.lineTo(px + CELL_PIXELS - pad, py + CELL_PIXELS - pad)
        ctx.closePath()
        ctx.fill()
    
    elif state.player_shape == "square":
        ctx.fillRect(px + pad, py + pad, size, size)
    
    elif state.player_shape == "rose":
        # Draw a beautiful rose using petals
        ctx.save()
        ctx.translate(center_x, center_y)
        
        # Draw multiple layers of petals for a realistic rose
        for layer in range(3):
            petal_count = 8 - layer * 2  # More petals in outer layers
            petal_size = size // 2 - layer * 4
            
            for i in range(petal_count):
                ctx.rotate(2 * 3.14159 / petal_count)
                ctx.fillStyle = state.player_color
                
                # Draw petal shape using ellipse
                ctx.beginPath()
                ctx.ellipse(0, -petal_size // 2, petal_size // 3, petal_size // 2, 0, 0, 2 * 3.14159)
                ctx.fill()
    
        # Draw center
        ctx.fillStyle = state.player_color
        ctx.beginPath()
        ctx.arc(0, 0, size // 8, 0, 2 * 3.14159)
        ctx.fill()
        
        ctx.restore()
    
    else:
        # Fallback to circle
        ctx.beginPath()
        ctx.arc(center_x, center_y, size // 2, 0, 2 * 3.14159)
        ctx.fill()
    
    # Reset shadow
    ctx.shadowBlur = 0

# ------------------------------ Game Logic ------------------------------

def can_move_to(from_x: int, from_y: int, dir_str: str) -> bool:
    w = state.maze_walls[(from_x, from_y)]
    if w[dir_str]:
        return False
    if dir_str == 'N':
        return from_y - 1 >= 0
    if dir_str == 'S':
        return from_y + 1 < state.grid_height
    if dir_str == 'W':
        return from_x - 1 >= 0
    if dir_str == 'E':
        return from_x + 1 < state.grid_width
    return False


def try_move(dir_str: str) -> None:
    if state.finished or state.maze_walls is None:
        return
    x, y = state.player_cell
    if not can_move_to(x, y, dir_str):
        return
    if dir_str == 'N':
        y -= 1
    elif dir_str == 'S':
        y += 1
    elif dir_str == 'W':
        x -= 1
    elif dir_str == 'E':
        x += 1
    state.player_cell = [x, y]
    render()
    check_win()


def check_win() -> None:
    if tuple(state.player_cell) == EXIT_POS:
        state.finished = True
        if state.start_time_s is not None:
            state.final_time_s = time.time() - state.start_time_s
        final_time_el.innerText = f"Time: {format_time_s(state.final_time_s)}s"
        set_overlay_visible(True)
        # auto submit once
        if not state.submitted:
            window.pyodide.runPythonAsync("await submit_score()")
            state.submitted = True


def render() -> None:
    if state.maze_walls is None:
        return
    draw_maze(state.maze_walls)
    draw_player(state.player_cell[0], state.player_cell[1])


async def reset_and_start() -> None:
    # Start new game with animated maze generation
    state.grid_width = GRID_SIZE
    state.grid_height = GRID_SIZE
    state.player_cell = list(START_POS)
    state.start_time_s = time.time()
    state.finished = False
    state.final_time_s = 0.0
    state.submitted = False
    
    # Preserve player color and shape when resetting
    if not state.player_color:
        state.player_color = DEFAULT_PLAYER_COLOR
    if not state.player_shape:
        state.player_shape = "circle"
    
    # Create colored player label with selected color and shape
    shape_symbols = {"circle": "●", "star": "★", "diamond": "◆", "triangle": "▲", "square": "■", "rose": "✿"}
    shape_symbol = shape_symbols.get(state.player_shape, "●")
    player_label_el.innerHTML = f'<span style="color: {state.player_color};">{shape_symbol}</span> {state.player_name}'
    timer_el.innerText = "00.00"
    set_overlay_visible(False)
    
    # Generate maze (animated or instant based on flag)
    try:
        if USE_ANIMATED_BUILD:
            state.maze_walls = await generate_maze_animated(state.grid_width, state.grid_height)
        else:
            state.maze_walls = generate_maze(state.grid_width, state.grid_height)
    except Exception:
        # Fallback to synchronous generation if animation fails
        state.maze_walls = generate_maze(state.grid_width, state.grid_height)
    
    render()

    # start ticking timer via requestAnimationFrame with persistent proxy
    def _tick(ts):
        if state.finished or state.start_time_s is None:
            return
        elapsed = time.time() - state.start_time_s
        timer_el.innerText = format_time_s(elapsed)
        window.requestAnimationFrame(_event_proxies['tick'])
    _event_proxies['tick'] = create_proxy(_tick)
    window.requestAnimationFrame(_event_proxies['tick'])

# ------------------------------ Input Handlers ------------------------------

def on_keydown(evt):
    key = evt.key.lower()
    if key in ['arrowup', 'w']:
        try_move('N')
    elif key in ['arrowdown', 's']:
        try_move('S')
    elif key in ['arrowleft', 'a']:
        try_move('W')
    elif key in ['arrowright', 'd']:
        try_move('E')


async def on_start_click(_e=None):
    if _e and hasattr(_e, 'preventDefault'):
        _e.preventDefault()
    name_input = document.getElementById('player-name')
    state.player_name = (name_input.value or 'Player').strip()
    
    # Get selected color and shape from JavaScript
    try:
        selected_color = window.getSelectedColor()
        state.player_color = selected_color
        selected_shape = window.getSelectedShape()
        state.player_shape = selected_shape
    except Exception:
        # Fallback to defaults if JavaScript fails
        state.player_color = DEFAULT_PLAYER_COLOR
        state.player_shape = "circle"
    
    show_screen('game-screen')
    
    # Show loading state on start button
    if start_btn:
        show_loading_state(start_btn, True)
    
    try:
        await reset_and_start()
    except Exception:
        # Fallback to synchronous version if async fails
        reset_and_start()
    finally:
        # Hide loading state
        if start_btn:
            show_loading_state(start_btn, False)


def on_start_click_sync(_e=None):
    # Synchronous fallback for start button
    if _e and hasattr(_e, 'preventDefault'):
        _e.preventDefault()
    name_input = document.getElementById('player-name')
    state.player_name = (name_input.value or 'Player').strip()
    
    # Get selected color and shape from JavaScript
    try:
        selected_color = window.getSelectedColor()
        state.player_color = selected_color
        selected_shape = window.getSelectedShape()
        state.player_shape = selected_shape
    except Exception:
        # Fallback to defaults if JavaScript fails
        state.player_color = DEFAULT_PLAYER_COLOR
        state.player_shape = "circle"
    
    show_screen('game-screen')
    reset_and_start()


def reset_leaderboard_state():
    # Reset leaderboard to initial state
    if leaderboard_loading_el:
        leaderboard_loading_el.classList.add("hidden")
    if leaderboard_table_el:
        leaderboard_table_el.classList.remove("hidden")
    if leaderboard_body_el:
        leaderboard_body_el.innerHTML = ""


def on_play_again(_e=None):
    show_screen('home-screen')
    set_overlay_visible(False)
    reset_leaderboard_state()


async def on_try_again(_e=None):
    set_overlay_visible(False)
    await reset_and_start()


def on_try_again_sync(_e=None):
    # Synchronous fallback for try again button
    set_overlay_visible(False)
    reset_and_start()

async def on_view_leaderboard(_e=None):
    # Load leaderboard with loading state
    # Ensure elements exist before proceeding
    if not leaderboard_loading_el or not leaderboard_table_el:
        print("Leaderboard elements not found")
        show_screen('leaderboard-screen')
        return
    
    print("Showing leaderboard loading state...")
    # Show loading state
    leaderboard_loading_el.classList.remove("hidden")
    leaderboard_table_el.classList.add("hidden")
    # Also toggle inline styles as a safety net
    leaderboard_loading_el.style.display = ""
    leaderboard_table_el.style.display = "none"
    
    # Load the leaderboard data
    await load_leaderboard()
    
    print("Leaderboard loaded, hiding loading state...")
    # Hide loading, show table with a small delay to ensure smooth transition
    await window.pyodide.runPythonAsync("import asyncio; await asyncio.sleep(0.1)")
    
    # Hide loading, show table
    leaderboard_loading_el.classList.add("hidden")
    leaderboard_table_el.classList.remove("hidden")
    # Also toggle inline styles as a safety net
    leaderboard_loading_el.style.display = "none"
    leaderboard_table_el.style.display = ""
    print("Loading state hidden, table shown")
    
    show_screen('leaderboard-screen')

# ------------------------------ Leaderboard ------------------------------
async def submit_score(_e=None):
    if _e and hasattr(_e, 'preventDefault'):
        _e.preventDefault()
    
    # Show loading state on submit button if available
    if view_leaderboard_btn:
        show_loading_state(view_leaderboard_btn, True)
    
    payload = {"name": state.player_name or "Player", "time": round(state.final_time_s, 2)}
    url = f"{API_BASE_URL}/submit_score"
    js_payload = to_js(payload, dict_converter=window.Object.fromEntries)
    body_str = JSON.stringify(js_payload)
    opts = {"method": "POST", "headers": {"Content-Type": "application/json"}, "body": body_str}
    opts_js = to_js(opts, dict_converter=window.Object.fromEntries)
    
    try:
        resp = await window.fetch(url, opts_js)
        # regardless of result, we don't block UI; leaderboard load happens when requested
    finally:
        # Hide loading state
        if view_leaderboard_btn:
            show_loading_state(view_leaderboard_btn, False)

async def load_leaderboard():
    # Load leaderboard data with proper error handling
    # Clear previous data
    if leaderboard_body_el:
        leaderboard_body_el.innerHTML = ""
    
    url = f"{API_BASE_URL}/leaderboard"
    
    async def _try_fetch_once():
        resp = await window.fetch(url)
        ok = bool(resp.ok)
        text = await resp.text()
        return ok, text
    
    try:
        ok, raw = await _try_fetch_once()
        if not ok:
            # Retry once after brief delay (handles transient reloads)
            await window.pyodide.runPythonAsync("import asyncio; await asyncio.sleep(0.2)")
            ok, raw = await _try_fetch_once()
            if not ok:
                print(f"Leaderboard fetch failed. Raw response: {raw[:200]}")
                if leaderboard_body_el:
                    leaderboard_body_el.innerHTML = "<tr><td colspan=3>Error loading leaderboard.</td></tr>"
                return
        # Parse JSON
        data = json.loads(raw)
    except Exception as e:
        print(f"Error loading leaderboard: {e}")
        if leaderboard_body_el:
            leaderboard_body_el.innerHTML = "<tr><td colspan=3>Error loading leaderboard.</td></tr>"
        return
    
    if not data:
        if leaderboard_body_el:
            leaderboard_body_el.innerHTML = "<tr><td colspan=3>No scores yet.</td></tr>"
        return
    
    # Build the leaderboard rows
    rows_html = []
    for idx, item in enumerate(data, start=1):
        # item may be JS object or dict after JSON parse; use .get defensively
        try:
            name = item.get('name', 'Player')
            time_val = float(item.get('time', 9999))
        except Exception:
            # Fallback if item is not a dict-like
            name = str(item['name']) if 'name' in item else 'Player'
            time_val = float(item['time']) if 'time' in item else 9999.0
        rows_html.append(f"<tr><td>{idx}</td><td>{name}</td><td>{time_val:.2f}</td></tr>")
    
    # Update the table
    if leaderboard_body_el:
        leaderboard_body_el.innerHTML = "".join(rows_html)

def initialize_leaderboard_state():
    # Initialize leaderboard to default state
    if leaderboard_loading_el:
        leaderboard_loading_el.classList.add("hidden")
    if leaderboard_table_el:
        leaderboard_table_el.classList.remove("hidden")
    if leaderboard_body_el:
        leaderboard_body_el.innerHTML = ""


# ------------------------------ Init ------------------------------

def bind_controls():
    # Keyboard
    _event_proxies['keydown'] = create_proxy(on_keydown)
    window.addEventListener('keydown', _event_proxies['keydown'])
    # Clicks (fallback if app loaded before JS boot)
    if btn_up: _event_proxies['btn_up'] = create_proxy(lambda e: try_move('N')); btn_up.addEventListener('click', _event_proxies['btn_up'])
    if btn_down: _event_proxies['btn_down'] = create_proxy(lambda e: try_move('S')); btn_down.addEventListener('click', _event_proxies['btn_down'])
    if btn_left: _event_proxies['btn_left'] = create_proxy(lambda e: try_move('W')); btn_left.addEventListener('click', _event_proxies['btn_left'])
    if btn_right: _event_proxies['btn_right'] = create_proxy(lambda e: try_move('E')); btn_right.addEventListener('click', _event_proxies['btn_right'])


def bind_ui():
    if start_btn:
        _event_proxies['start'] = create_proxy(lambda e: window.pyodide.runPythonAsync("await on_start_click()"))
        start_btn.addEventListener('click', _event_proxies['start'])
    if home_leaderboard_btn:
        _event_proxies['home_lb'] = create_proxy(lambda e: window.pyodide.runPythonAsync("await on_view_leaderboard()"))
        home_leaderboard_btn.addEventListener('click', _event_proxies['home_lb'])
    if play_again_btn:
        _event_proxies['play_again'] = create_proxy(on_play_again)
        play_again_btn.addEventListener('click', _event_proxies['play_again'])
    if view_leaderboard_btn:
        _event_proxies['view_lb'] = create_proxy(lambda e: window.pyodide.runPythonAsync("await on_view_leaderboard()"))
        view_leaderboard_btn.addEventListener('click', _event_proxies['view_lb'])
    if try_again_btn:
        _event_proxies['try_again'] = create_proxy(lambda e: window.pyodide.runPythonAsync("await on_try_again()"))
        try_again_btn.addEventListener('click', _event_proxies['try_again'])
    bind_controls()
    
    # Initialize leaderboard state
    initialize_leaderboard_state()

bind_ui()
show_screen('home-screen')
`;

        // Enhanced loading with better error handling
        (async () => {
            const progressBar = document.getElementById('loading-progress');
            const loadingScreen = document.getElementById('loading-screen');
            const homeScreen = document.getElementById('home-screen');
            
            let progress = 0;
            let progressInterval;
            
            try {
                console.log('Starting Pyodide initialization...');
                
                // Start progress simulation
                progressInterval = setInterval(() => {
                    progress += Math.random() * 5; // Slower progress for real loading
                    if (progress >= 90) progress = 90; // Cap at 90% until actually loaded
                    progressBar.style.width = progress + '%';
                }, 200);
                
                // Load Pyodide with timeout
                console.log('Loading Pyodide runtime...');
                const timeoutPromise = new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Pyodide load timeout')), 30000)
                );
                
                const pyodide = await Promise.race([
                    loadPyodide({
                        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
                    }),
                    timeoutPromise
                ]);
                
                console.log('Pyodide loaded successfully');
                window.pyodide = pyodide;
                
                // Complete progress bar
                clearInterval(progressInterval);
                progressBar.style.width = '95%';
                
                console.log('Running Python game code...');
                await pyodide.runPythonAsync(PYTHON_GAME_CODE);
                
                console.log('Game initialized successfully!');
                
                // Final progress and transition
                progressBar.style.width = '100%';
                setTimeout(() => {
                    loadingScreen.classList.remove('active');
                    homeScreen.classList.add('active');
                }, 500);
                
            } catch (err) {
                console.error('Failed to initialize game:', err);
                clearInterval(progressInterval);
                
                // Show error to user
                const loadingCard = loadingScreen.querySelector('.card');
                loadingCard.innerHTML = `
                    <h1>Maze Runner</h1>
                    <p style="color: #ef4444; margin: 20px 0;">
                        ❌ Failed to load game runtime
                    </p>
                    <p style="font-size: 14px; color: #94a3b8;">
                        Error: ${err.message}<br>
                        Please check your internet connection and try refreshing the page.
                    </p>
                    <button onclick="location.reload()" style="margin-top: 16px;">
                        🔄 Try Again
                    </button>
                `;
            }
        })();
    </script>
</body>
</html>"""


def get_leaderboard_scores() -> List[Dict[str, Any]]:
    """Get best scores from database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, MIN(time) as best_time 
        FROM scores 
        GROUP BY name 
        ORDER BY best_time ASC
        LIMIT 50
    ''')
    
    results = cursor.fetchall()
    conn.close()
    scores = []
    for name, time_val in results:
        scores.append({
            "name": name,
            "time": round(float(time_val), 2)
        })
    
    return scores

def save_score(name: str, time_val: float) -> bool:
    """Save a score to database"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO scores (name, time) VALUES (?, ?)",
            (name.strip(), round(float(time_val), 2))
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving score: {e}")
        return False

@app.get("/", response_class=HTMLResponse)
async def serve_game():
    """Serve the main game page"""
    return HTMLResponse(content=HTML_TEMPLATE)

@app.post("/api/submit_score")
async def submit_score(score: ScoreIn) -> Dict[str, str]:
    """Submit a score to the leaderboard"""
    try:
        success = save_score(score.name, score.time)
        if success:
            return {"status": "ok"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save score")
    except Exception as exc:
        print(f"Error submitting score: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/leaderboard")
async def get_leaderboard() -> JSONResponse:
    """Get the leaderboard data"""
    try:
        scores = get_leaderboard_scores()
        return JSONResponse(content=scores)
    except Exception as exc:
        print(f"Error getting leaderboard: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

def main():
    """Run the standalone maze game server"""
    import os
    port = int(os.environ.get("PORT", PORT))
    host = os.environ.get("HOST", HOST)
    
    print("🎮 Starting Maze Runner Game Server...")
    print(f"🌐 Game will be available at: http://{host}:{port}")
    print("🎯 Press Ctrl+C to stop the server")
    print("💾 Using SQLite database for persistent leaderboard storage")
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Thanks for playing!")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()