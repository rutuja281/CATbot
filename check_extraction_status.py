#!/usr/bin/env python3
"""Quick status check for question extraction"""
from database import Database

db = Database()
questions = db.get_all_questions()

print("=" * 60)
print("QUESTION BANK STATUS")
print("=" * 60)
print(f"Total Questions: {len(questions)}")
print()

# Group by source document
sources = {}
for q in questions:
    source = q.get('source_document', 'Unknown')
    sources[source] = sources.get(source, 0) + 1

print("Questions by Source Document:")
for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
    print(f"  {source}: {count}")

print()
print("Questions by Topic:")
topics = {}
for q in questions:
    topic = q.get('topic_name', 'Unknown')
    topics[topic] = topics.get(topic, 0) + 1

for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {topic}: {count}")

print("=" * 60)

