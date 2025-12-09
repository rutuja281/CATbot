from typing import List, Dict, Optional
from database import Database
import random
import math

class AdaptiveQuestionSelector:
    def __init__(self, db: Database):
        self.db = db
    
    def get_user_difficulty_rating(self, user_id: str, topic_id: Optional[int] = None) -> float:
        """Calculate user's current difficulty rating based on performance"""
        attempts = self.db.get_user_attempts(user_id, limit=50)
        
        if not attempts:
            return 3.0  # Default medium difficulty
        
        # Filter by topic if specified (need to check question's topic)
        if topic_id:
            filtered_attempts = []
            for a in attempts:
                q = self.db.get_question(a['question_id'])
                if q and q.get('topic_id') == topic_id:
                    filtered_attempts.append(a)
            attempts = filtered_attempts
        
        if not attempts:
            return 3.0
        
        # Calculate recent performance
        recent_attempts = attempts[:20]  # Last 20 attempts
        correct_count = sum(1 for a in recent_attempts if a['is_correct'] == 1)
        accuracy = correct_count / len(recent_attempts) if recent_attempts else 0.5
        
        # Calculate average time (normalized)
        avg_time = sum(a.get('time_taken_sec', 120) or 120 for a in recent_attempts) / len(recent_attempts)
        
        # Start with base rating
        rating = 3.0
        
        # Adjust based on accuracy
        if accuracy < 0.4:  # Less than 40% correct
            rating -= 0.8
        elif accuracy < 0.6:  # 40-60% correct
            rating -= 0.4
        elif accuracy > 0.8:  # More than 80% correct
            rating += 0.6
        elif accuracy > 0.9:  # More than 90% correct
            rating += 1.0
        
        # Adjust based on speed (faster = higher rating)
        if avg_time < 60:  # Very fast
            rating += 0.3
        elif avg_time > 180:  # Very slow
            rating -= 0.3
        
        # Clamp between 1 and 5
        return max(1.0, min(5.0, rating))
    
    def get_weak_topics(self, user_id: str) -> List[Dict]:
        """Get topics where user performs poorly"""
        stats = self.db.get_user_stats(user_id)
        weak_topics = []
        
        for topic_stat in stats.get('topic_stats', []):
            attempts = topic_stat.get('attempts', 0)
            correct = topic_stat.get('correct', 0)
            if attempts > 0:
                accuracy = correct / attempts
                if accuracy < 0.6:  # Less than 60% accuracy
                    weak_topics.append({
                        'topic': topic_stat['topic_name'],
                        'accuracy': accuracy,
                        'attempts': attempts
                    })
        
        # Sort by accuracy (lowest first)
        weak_topics.sort(key=lambda x: x['accuracy'])
        return weak_topics
    
    def select_next_question(self, user_id: str, topic_id: Optional[int] = None) -> Optional[Dict]:
        """Select the next adaptive question for the user"""
        # Get user's current difficulty rating
        user_rating = self.get_user_difficulty_rating(user_id, topic_id)
        
        # Get all questions
        all_questions = self.db.get_all_questions(topic_id)
        
        if not all_questions:
            return None
        
        # Get questions user hasn't attempted
        attempted_ids = {a['question_id'] for a in self.db.get_user_attempts(user_id)}
        unattempted = [q for q in all_questions if q['id'] not in attempted_ids]
        
        # If user has attempted all questions, use all questions
        if not unattempted:
            unattempted = all_questions
        
        # Score each question based on:
        # 1. Difficulty match with user rating
        # 2. Whether it's unattempted (prefer new questions)
        # 3. Topic weakness (prefer weak topics)
        
        weak_topics = {wt['topic'] for wt in self.get_weak_topics(user_id)}
        
        scored_questions = []
        for q in unattempted:
            score = 0.0
            
            # Difficulty match (closer to user rating = higher score)
            diff_diff = abs(q['difficulty_score'] - user_rating)
            score += (5.0 - diff_diff) * 2  # Prefer questions close to user rating
            
            # Prefer unattempted questions
            if q['id'] not in attempted_ids:
                score += 10.0
            
            # Prefer weak topics
            if q['topic_name'] in weak_topics:
                score += 5.0
            
            # Slight randomness to avoid always same question
            score += random.uniform(0, 2.0)
            
            scored_questions.append((score, q))
        
        # Sort by score and pick top question
        scored_questions.sort(key=lambda x: x[0], reverse=True)
        
        if scored_questions:
            return scored_questions[0][1]
        
        return None
    
    def get_adaptive_difficulty(self, user_id: str, topic_id: Optional[int] = None) -> float:
        """Get the difficulty level for next question"""
        user_rating = self.get_user_difficulty_rating(user_id, topic_id)
        
        # Add some variation (±0.5) to keep it interesting
        target_difficulty = user_rating + random.uniform(-0.5, 0.5)
        return max(1.0, min(5.0, target_difficulty))

