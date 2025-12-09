import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json

class Database:
    def __init__(self, db_path: str = "catbot.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table (using session-based anonymous users)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Topics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL
            )
        """)
        
        # Questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                question_text TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                difficulty_score REAL DEFAULT 3.0,
                estimated_time_sec INTEGER DEFAULT 120,
                source_document TEXT,
                source_page INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id)
            )
        """)
        
        # Attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                question_id INTEGER NOT NULL,
                is_correct INTEGER NOT NULL,
                time_taken_sec INTEGER,
                user_answer TEXT,
                attempt_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                test_id INTEGER,
                FOREIGN KEY (question_id) REFERENCES questions(id),
                FOREIGN KEY (test_id) REFERENCES tests(id)
            )
        """)
        
        # Tests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                test_type TEXT NOT NULL,
                total_questions INTEGER,
                score INTEGER,
                total_time_sec INTEGER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Initialize default topics
        default_topics = [
            ("Arithmetic", "Quantitative"),
            ("Algebra", "Quantitative"),
            ("Geometry", "Quantitative"),
            ("Number Systems", "Quantitative"),
            ("Data Interpretation", "Quantitative"),
            ("Logical Reasoning", "Verbal"),
            ("Reading Comprehension", "Verbal"),
            ("Para Jumbles", "Verbal"),
            ("Vocabulary", "Verbal"),
        ]
        
        for topic_name, category in default_topics:
            cursor.execute("""
                INSERT OR IGNORE INTO topics (name, category) 
                VALUES (?, ?)
            """, (topic_name, category))
        
        conn.commit()
        conn.close()
    
    # User methods
    def get_or_create_user(self, user_id: str) -> str:
        """Get or create a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return user_id
    
    # Question methods
    def add_question(self, topic_name: str, question_text: str, options: List[str], 
                     correct_answer: str, explanation: str = "", difficulty_score: float = 3.0,
                     estimated_time_sec: int = 120, source_document: str = "", 
                     source_page: int = 0) -> int:
        """Add a question to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get topic ID
        cursor.execute("SELECT id FROM topics WHERE name = ?", (topic_name,))
        topic_row = cursor.fetchone()
        if not topic_row:
            # Create topic if it doesn't exist
            cursor.execute("INSERT INTO topics (name, category) VALUES (?, ?)", 
                         (topic_name, "General"))
            topic_id = cursor.lastrowid
        else:
            topic_id = topic_row[0]
        
        # Store options as JSON
        options_json = json.dumps(options)
        
        cursor.execute("""
            INSERT INTO questions 
            (topic_id, question_text, options, correct_answer, explanation, 
             difficulty_score, estimated_time_sec, source_document, source_page)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (topic_id, question_text, options_json, correct_answer, explanation,
              difficulty_score, estimated_time_sec, source_document, source_page))
        
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return question_id
    
    def get_question(self, question_id: int) -> Optional[Dict]:
        """Get a question by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.*, t.name as topic_name, t.category as topic_category
            FROM questions q
            JOIN topics t ON q.topic_id = t.id
            WHERE q.id = ?
        """, (question_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'topic_id': row['topic_id'],
                'topic_name': row['topic_name'],
                'topic_category': row['topic_category'],
                'question_text': row['question_text'],
                'options': json.loads(row['options']),
                'correct_answer': row['correct_answer'],
                'explanation': row['explanation'],
                'difficulty_score': row['difficulty_score'],
                'estimated_time_sec': row['estimated_time_sec'],
                'source_document': row['source_document'],
                'source_page': row['source_page']
            }
        return None
    
    def get_all_questions(self, topic_id: Optional[int] = None) -> List[Dict]:
        """Get all questions, optionally filtered by topic"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if topic_id:
            cursor.execute("""
                SELECT q.*, t.name as topic_name, t.category as topic_category
                FROM questions q
                JOIN topics t ON q.topic_id = t.id
                WHERE q.topic_id = ?
                ORDER BY q.id
            """, (topic_id,))
        else:
            cursor.execute("""
                SELECT q.*, t.name as topic_name, t.category as topic_category
                FROM questions q
                JOIN topics t ON q.topic_id = t.id
                ORDER BY q.id
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row['id'],
            'topic_id': row['topic_id'],
            'topic_name': row['topic_name'],
            'topic_category': row['topic_category'],
            'question_text': row['question_text'],
            'options': json.loads(row['options']),
            'correct_answer': row['correct_answer'],
            'explanation': row['explanation'],
            'difficulty_score': row['difficulty_score'],
            'estimated_time_sec': row['estimated_time_sec'],
            'source_document': row['source_document'],
            'source_page': row['source_page']
        } for row in rows]
    
    # Attempt methods
    def record_attempt(self, user_id: str, question_id: int, is_correct: bool,
                      time_taken_sec: Optional[int] = None, user_answer: str = "",
                      test_id: Optional[int] = None) -> int:
        """Record a user's attempt at a question"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attempts 
            (user_id, question_id, is_correct, time_taken_sec, user_answer, test_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, question_id, 1 if is_correct else 0, time_taken_sec, 
              user_answer, test_id))
        attempt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return attempt_id
    
    def get_user_attempts(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get user's recent attempts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, q.question_text, q.difficulty_score, t.name as topic_name
            FROM attempts a
            JOIN questions q ON a.question_id = q.id
            JOIN topics t ON q.topic_id = t.id
            WHERE a.user_id = ?
            ORDER BY a.attempt_at DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # Test methods
    def create_test(self, user_id: str, test_type: str, total_questions: int) -> int:
        """Create a new test session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tests (user_id, test_type, total_questions, started_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, test_type, total_questions))
        test_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return test_id
    
    def complete_test(self, test_id: int, score: int, total_time_sec: int):
        """Mark a test as completed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tests 
            SET score = ?, total_time_sec = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (score, total_time_sec, test_id))
        conn.commit()
        conn.close()
    
    def get_user_tests(self, user_id: str) -> List[Dict]:
        """Get all tests for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM tests 
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # Analytics methods
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total attempts and accuracy
        cursor.execute("""
            SELECT 
                COUNT(*) as total_attempts,
                SUM(is_correct) as correct_attempts,
                AVG(time_taken_sec) as avg_time
            FROM attempts
            WHERE user_id = ?
        """, (user_id,))
        stats = cursor.fetchone()
        
        # Topic-wise performance
        cursor.execute("""
            SELECT 
                t.name as topic_name,
                COUNT(*) as attempts,
                SUM(a.is_correct) as correct,
                AVG(a.time_taken_sec) as avg_time
            FROM attempts a
            JOIN questions q ON a.question_id = q.id
            JOIN topics t ON q.topic_id = t.id
            WHERE a.user_id = ?
            GROUP BY t.name
            ORDER BY attempts DESC
        """, (user_id,))
        topic_stats = cursor.fetchall()
        
        # Streak calculation
        cursor.execute("""
            SELECT DATE(attempt_at) as date, SUM(is_correct) as correct_count
            FROM attempts
            WHERE user_id = ?
            GROUP BY DATE(attempt_at)
            ORDER BY date DESC
            LIMIT 30
        """, (user_id,))
        daily_stats = cursor.fetchall()
        
        conn.close()
        
        total = stats['total_attempts'] or 0
        correct = stats['correct_attempts'] or 0
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Calculate streak
        streak = 0
        if daily_stats:
            for i, day in enumerate(daily_stats):
                if day['correct_count'] > 0:
                    if i == 0:
                        streak = 1
                    elif (datetime.strptime(daily_stats[i-1]['date'], '%Y-%m-%d') - 
                          datetime.strptime(day['date'], '%Y-%m-%d')).days == 1:
                        streak += 1
                    else:
                        break
        
        return {
            'total_attempts': total,
            'correct_attempts': correct,
            'accuracy': accuracy,
            'avg_time': stats['avg_time'] or 0,
            'streak': streak,
            'topic_stats': [dict(row) for row in topic_stats]
        }
    
    def get_questions_not_attempted(self, user_id: str, topic_id: Optional[int] = None) -> List[int]:
        """Get question IDs that user hasn't attempted"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if topic_id:
            cursor.execute("""
                SELECT q.id FROM questions q
                WHERE q.topic_id = ? 
                AND q.id NOT IN (
                    SELECT question_id FROM attempts WHERE user_id = ?
                )
            """, (topic_id, user_id))
        else:
            cursor.execute("""
                SELECT q.id FROM questions q
                WHERE q.id NOT IN (
                    SELECT question_id FROM attempts WHERE user_id = ?
                )
            """, (user_id,))
        
        question_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return question_ids

