import json
import pandas as pd
import streamlit as st
from typing import List, Dict, Any
import re

class DataIngester:
    """Handles dynamic data ingestion from various file formats"""
    
    def __init__(self):
        self.supported_formats = ['.json', '.csv', '.txt']
    
    def safe_json_load(self, file_content):
        """Safely load JSON content with comprehensive error handling"""
        try:
            return json.loads(file_content)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {e}")
            return None
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            return None
    
    def read_csv_with_encoding(self, uploaded_file):
        """Read CSV file with multiple encoding attempts"""
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
        
        for encoding in encodings:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding=encoding)
                st.sidebar.success(f"Read with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                st.error(f"Error with {encoding}: {e}")
                continue
        
        # Final attempt with error handling
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='utf-8', errors='replace')
            st.sidebar.warning("Used error replacement for problematic characters")
            return df
        except Exception as e:
            st.error(f"Final CSV read attempt failed: {e}")
            return None
    
    def extract_rating_from_text(self, rating_text):
        """Extract numeric rating from various rating formats"""
        if not rating_text or pd.isna(rating_text):
            return 3
        
        rating_str = str(rating_text).lower()
        
        # Extract from patterns like "★★★☆☆ (3 stars)"
        star_match = re.search(r'\((\d+)\s*stars?\)', rating_str)
        if star_match:
            return int(star_match.group(1))
        
        # Count stars ★
        star_count = rating_str.count('★')
        if star_count > 0:
            return star_count
        
        # Count asterisks *
        asterisk_count = rating_str.count('*')
        if asterisk_count > 0:
            return asterisk_count
        
        # Try to extract numeric value
        num_match = re.search(r'(\d+(?:\.\d+)?)/?(\d+)?', rating_str)
        if num_match:
            numerator = float(num_match.group(1))
            if num_match.group(2):  # If denominator exists (e.g., 4/5)
                denominator = float(num_match.group(2))
                return (numerator / denominator) * 5
            return min(numerator, 5)  # Cap at 5
        
        return 3  # Default neutral rating
    
    def normalize_review(self, raw_data, index):
        """Normalize various review formats to standard structure"""
        try:
            if isinstance(raw_data, dict):
                # Handle dictionary format
                return {
                    'review_id': str(raw_data.get('review_id', raw_data.get('id', f'R{index:05d}'))),
                    'date': str(raw_data.get('date', raw_data.get('timestamp', ''))),
                    'rating_text': str(raw_data.get('rating', raw_data.get('stars', raw_data.get('score', '')))),
                    'text': str(raw_data.get('text', raw_data.get('review', raw_data.get('content', '')))),
                    'raw_data': raw_data
                }
            elif isinstance(raw_data, str):
                # Handle plain text reviews
                return {
                    'review_id': f'R{index:05d}',
                    'date': '',
                    'rating_text': '',
                    'text': raw_data,
                    'raw_data': raw_data
                }
            else:
                # Handle other formats
                return {
                    'review_id': f'R{index:05d}',
                    'date': '',
                    'rating_text': '',
                    'text': str(raw_data),
                    'raw_data': raw_data
                }
        except Exception as e:
            return {
                'review_id': f'R{index:05d}',
                'date': '',
                'rating_text': '',
                'text': f'Error processing: {e}',
                'raw_data': raw_data
            }
    
    def ingest_json(self, uploaded_file):
        """Ingest and parse JSON files"""
        try:
            content = uploaded_file.getvalue().decode('utf-8')
            data = self.safe_json_load(content)
            
            if not data:
                return []
            
            reviews = []
            
            # Handle different JSON structures
            if isinstance(data, list):
                for i, item in enumerate(data):
                    normalized = self.normalize_review(item, i)
                    reviews.append(normalized)
            elif isinstance(data, dict):
                if 'reviews' in data and isinstance(data['reviews'], list):
                    for i, item in enumerate(data['reviews']):
                        normalized = self.normalize_review(item, i)
                        reviews.append(normalized)
                else:
                    normalized = self.normalize_review(data, 0)
                    reviews.append(normalized)
            
            return reviews
            
        except Exception as e:
            st.error(f"JSON ingestion error: {e}")
            return []
    
    def ingest_csv(self, uploaded_file):
        """Ingest and parse CSV files"""
        try:
            df = self.read_csv_with_encoding(uploaded_file)
            if df is None:
                return []
            
            reviews = []
            for i, row in df.iterrows():
                review_dict = {}
                for col in df.columns:
                    value = row[col]
                    review_dict[col] = '' if pd.isna(value) else str(value)
                
                normalized = self.normalize_review(review_dict, i)
                reviews.append(normalized)
            
            return reviews
            
        except Exception as e:
            st.error(f"CSV ingestion error: {e}")
            return []
    
    def ingest_text(self, uploaded_file):
        """Ingest plain text files"""
        try:
            content = uploaded_file.getvalue().decode('utf-8')
            reviews = []
            
            # Split by lines or paragraphs
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip():  # Only non-empty lines
                    normalized = self.normalize_review(line.strip(), i)
                    reviews.append(normalized)
            
            return reviews
            
        except Exception as e:
            st.error(f"Text file ingestion error: {e}")
            return []
    
    def ingest_file(self, uploaded_file):
        """Main ingestion method"""
        if uploaded_file is None:
            return []
        
        filename = uploaded_file.name.lower()
        
        try:
            if filename.endswith('.json'):
                return self.ingest_json(uploaded_file)
            elif filename.endswith('.csv'):
                return self.ingest_csv(uploaded_file)
            elif filename.endswith('.txt'):
                return self.ingest_text(uploaded_file)
            else:
                st.error(f"Unsupported file format: {filename}")
                return []
                
        except Exception as e:
            st.error(f"File ingestion failed: {e}")
            return []