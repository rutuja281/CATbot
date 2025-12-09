# Quick Start Guide - CAT Exam Prep Platform

## 🎯 New Features

Your CAT Exam Prep platform now includes:

1. **📥 Question Extraction** - Extract questions from PDF documents automatically
2. **📊 Progress Dashboard** - Track your performance, accuracy, and streaks
3. **🎯 Adaptive Practice** - AI-powered adaptive questions based on your skill level
4. **📝 Mock Tests** - Take timed mock tests to assess your preparation
5. **💬 Chat Assistant** - Original RAG chatbot for explanations

## 🚀 Getting Started

### Step 1: Extract Questions from Your PDFs

1. Go to **"📥 Extract Questions"** tab
2. Upload your CAT exam PDF files (the ones in your `data/` folder)
3. Click **"🔍 Extract Questions"**
4. Wait for the system to extract questions (this uses OpenAI API)
5. Questions will be automatically added to the question bank with difficulty scores

### Step 2: Start Practicing

1. Go to **"🎯 Adaptive Practice"** tab
2. Click **"🔄 Get New Question"**
3. Answer the question
4. The system will:
   - Track your performance
   - Adjust difficulty based on your answers
   - Focus on your weak areas

### Step 3: Track Your Progress

1. Go to **"📊 Dashboard"** tab
2. View:
   - Overall accuracy and performance
   - Topic-wise breakdown
   - Areas needing improvement
   - Your solving streak

### Step 4: Take Mock Tests

1. Go to **"📝 Mock Test"** tab
2. Select number of questions and test type
3. Click **"🚀 Start Mock Test"**
4. Answer all questions
5. View your score and performance

## 📋 How It Works

### Question Extraction
- Uses GPT to extract questions from PDFs
- Automatically scores difficulty (1-5 scale)
- Categorizes by topic
- Stores in SQLite database

### Adaptive Algorithm
- Tracks your performance on each question
- Calculates your skill level
- Suggests questions at appropriate difficulty
- Focuses on weak topics

### Difficulty Scoring
Based on:
- Question length
- Number of options
- Topic complexity
- Estimated solving time

## 💡 Tips

1. **Extract questions first** - Build your question bank before practicing
2. **Practice regularly** - Maintain your streak for better tracking
3. **Review weak areas** - Dashboard shows where you need improvement
4. **Take mock tests** - Simulate exam conditions

## 🔧 Troubleshooting

### No questions extracted?
- Check that PDFs contain actual questions
- Ensure OpenAI API key is valid
- Check console for extraction errors

### Not enough questions for mock test?
- Extract more questions from PDFs
- Minimum 5 questions needed for a test

### Questions seem too easy/hard?
- The system adapts over time
- Answer more questions for better adaptation
- Difficulty adjusts based on your accuracy

## 📊 Database

All data is stored locally in `catbot.db`:
- Questions
- Your attempts
- Test results
- Performance statistics

This file is in `.gitignore` so it won't be uploaded to GitHub.

## 🎓 Next Steps

1. Extract questions from all your PDFs
2. Practice daily to build your streak
3. Take weekly mock tests
4. Review dashboard to identify weak areas
5. Use chat assistant for explanations

Happy studying! 🚀

