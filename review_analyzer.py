import re
from textblob import TextBlob
from typing import Dict, Any, List
import pandas as pd

class ReviewAnalyzer:
    """
    A robust analyzer that handles various data types and formats
    """
    
    def __init__(self):
        self.suggestion_patterns = [
            r"please ([\w\s]+)",
            r"they should ([\w\s]+)", 
            r"you should ([\w\s]+)",
            r"we should ([\w\s]+)",
            r"add ([\w\s]+)",
            r"implement ([\w\s]+)",
            r"improve ([\w\s]+)",
            r"make ([\w\s]+)",
            r"fix ([\w\s]+)",
            r"i suggest ([\w\s]+)",
            r"it would be great if ([\w\s]+)",
            r"can you ([\w\s]+)",
            r"could you ([\w\s]+)"
        ]
        
        self.problem_keywords = [
            'frustrating', 'slow', 'late', 'missing', 'broken',
            'confusing', 'difficult', 'bad', 'poor', 'terrible',
            'awful', 'problem', 'issue', 'error', 'bug', 'crash',
            'not working', 'doesn\'t work', 'failed', 'disappointing',
            'horrible', 'useless', 'waste', 'never', 'again'
        ]
        
        self.topic_keywords = [
            'app', 'delivery', 'food', 'order', 'payment',
            'search', 'discount', 'price', 'quality', 'service',
            'support', 'interface', 'navigation', 'checkout',
            'shipping', 'rider', 'driver', 'product', 'website',
            'mobile', 'customer', 'experience', 'package', 'item'
        ]

    def safe_string_conversion(self, value):
        """Safely convert any value to string"""
        if value is None:
            return ""
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, str):
            return value
        try:
            return str(value)
        except:
            return ""

    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment using TextBlob with error handling"""
        try:
            clean_text = self.safe_string_conversion(text)
            if not clean_text.strip():
                return "neutral"
                
            analysis = TextBlob(clean_text)
            polarity = analysis.sentiment.polarity
            
            if polarity > 0.2:
                return "positive"
            elif polarity < -0.2:
                return "negative"
            else:
                return "neutral"
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return "neutral"

    def extract_suggestions(self, text: str) -> List[str]:
        """Extract suggestions using regex patterns"""
        suggestions = []
        try:
            clean_text = self.safe_string_conversion(text).lower()
            if not clean_text.strip():
                return []
                
            for pattern in self.suggestion_patterns:
                matches = re.finditer(pattern, clean_text)
                for match in matches:
                    suggestion = match.group(1).strip()
                    if suggestion and len(suggestion) > 3:  # Minimum length
                        suggestions.append(suggestion.capitalize())
            return list(set(suggestions))  # Remove duplicates
        except Exception as e:
            print(f"Suggestion extraction error: {e}")
            return []

    def extract_problems(self, text: str) -> List[str]:
        """Extract problems using keyword matching"""
        problems = []
        try:
            clean_text = self.safe_string_conversion(text).lower()
            if not clean_text.strip():
                return []
                
            sentences = re.split(r'[.!?]', clean_text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                for keyword in self.problem_keywords:
                    if keyword in sentence:
                        # Clean up and capitalize the sentence
                        clean_sentence = sentence.capitalize()
                        if clean_sentence not in problems:
                            problems.append(clean_sentence)
                        break
            
            return problems[:5]  # Return max 5 problems
        except Exception as e:
            print(f"Problem extraction error: {e}")
            return []

    def extract_topics(self, text: str) -> List[str]:
        """Extract topics using keyword matching"""
        topics = set()
        try:
            clean_text = self.safe_string_conversion(text).lower()
            if not clean_text.strip():
                return []
                
            # Check for single keywords
            for keyword in self.topic_keywords:
                if keyword in clean_text:
                    topics.add(keyword.capitalize())
            
            # Check for common phrases
            common_phrases = [
                'discount program', 'search functionality', 
                'delivery time', 'customer support',
                'user interface', 'checkout process',
                'food quality', 'order accuracy',
                'mobile app', 'website design',
                'payment process', 'shipping speed'
            ]
            
            for phrase in common_phrases:
                if phrase in clean_text:
                    topics.add(phrase.title())
            
            return sorted(list(topics))
        except Exception as e:
            print(f"Topic extraction error: {e}")
            return []

    def extract_rating(self, rating_value):
        """Extract numeric rating from various formats"""
        try:
            rating_str = self.safe_string_conversion(rating_value)
            
            # Try to extract number from parentheses (e.g., "★★★☆☆ (3 stars)" -> 3)
            import re
            number_match = re.search(r'\((\d+)', rating_str)
            if number_match:
                return int(number_match.group(1))
            
            # Try to count stars
            star_count = rating_str.count('★')
            if star_count > 0:
                return star_count
            
            # Try to parse as float
            try:
                return float(rating_str)
            except:
                pass
                
            # Default to 3 if cannot parse
            return 3
        except:
            return 3

    def analyze_review_text(self, review_text: str, review_data: Dict = None) -> Dict[str, Any]:
        """
        Analyze review text with comprehensive error handling
        """
        try:
            # Perform analysis
            sentiment = self.analyze_sentiment(review_text)
            topics = self.extract_topics(review_text)
            problems = self.extract_problems(review_text)
            suggestions = self.extract_suggestions(review_text)
            
            # Extract rating if review_data is provided
            numeric_rating = 3
            if review_data and isinstance(review_data, dict):
                rating_value = review_data.get('rating', '')
                numeric_rating = self.extract_rating(rating_value)

            return {
                "sentiment": sentiment,
                "topics": topics,
                "problems": problems,
                "suggestions": suggestions,
                "numeric_rating": numeric_rating,
                "character_count": len(review_text),
                "word_count": len(review_text.split()),
                "analysis_success": True
            }
        except Exception as e:
            print(f"Review analysis failed: {e}")
            return self.get_default_insights(review_text)

    def get_default_insights(self, text=""):
        """Return default insights when analysis fails"""
        text_str = self.safe_string_conversion(text)
        return {
            "sentiment": "neutral",
            "topics": [],
            "problems": [],
            "suggestions": [],
            "numeric_rating": 3,
            "character_count": len(text_str),
            "word_count": len(text_str.split()),
            "analysis_success": False
        }

    def analyze_batch(self, reviews_data: List[Dict]) -> pd.DataFrame:
        """Analyze a batch of reviews and return DataFrame"""
        analyzed_reviews = []
        
        for i, review in enumerate(reviews_data):
            # Ensure review is a dictionary
            if not isinstance(review, dict):
                print(f"Warning: Review {i} is not a dictionary: {review}")
                continue
                
            # Extract text safely
            review_text = self.safe_string_conversion(
                review.get('text', review.get('review', review.get('content', '')))
            )
            
            insights = self.analyze_review_text(review_text, review)
            
            # Create combined result
            result = {
                'review_id': self.safe_string_conversion(review.get('review_id', review.get('id', f'R{i:05d}'))),
                'date': self.safe_string_conversion(review.get('date', review.get('timestamp', ''))),
                'original_rating': self.safe_string_conversion(review.get('rating', '')),
                'text': review_text,
                **insights
            }
            analyzed_reviews.append(result)
        
        return pd.DataFrame(analyzed_reviews)