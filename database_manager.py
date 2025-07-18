import pymongo
from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict, Optional
import os

class DatabaseManager:
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", database_name: str = "meeting_summarizer"):
        """
        Initialize the database manager.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
        self.collection = None
        self.connect()
    
    def connect(self):
        """Connect to MongoDB and create database/collection if not exists."""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self.collection = self.db["transcription_history"]
            
            # Create indexes for better performance
            self.collection.create_index("timestamp", pymongo.DESCENDING)
            self.collection.create_index("audio_filename")
            
            print(f"Connected to MongoDB database: {self.database_name}")
            return True
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return False
    
    def save_transcription(self, audio_filename: str, transcript: str, summary: str, 
                         whisper_model: str, llm_model: str, context: str = "") -> str:
        """
        Save a transcription record to the database.
        
        Args:
            audio_filename: Original audio filename
            transcript: The transcribed text
            summary: The generated summary
            whisper_model: Whisper model used
            llm_model: LLM model used for summarization
            context: Optional context provided by user
            
        Returns:
            str: The ID of the saved record
        """
        try:
            record = {
                "audio_filename": audio_filename,
                "transcript": transcript,
                "summary": summary,
                "whisper_model": whisper_model,
                "llm_model": llm_model,
                "context": context,
                "timestamp": datetime.now(),
                "audio_duration": self._get_audio_duration(transcript),
                "transcript_length": len(transcript),
                "summary_length": len(summary)
            }
            
            result = self.collection.insert_one(record)
            print(f"Transcription saved with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error saving transcription: {e}")
            return None
    
    def get_all_transcriptions(self) -> List[Dict]:
        """
        Get all transcription records from the database.
        
        Returns:
            List of transcription records
        """
        try:
            # Sort by timestamp in descending order (newest first)
            records = list(self.collection.find().sort("timestamp", -1))
            
            # Convert ObjectId to string for JSON serialization
            for record in records:
                record["_id"] = str(record["_id"])
                # Format timestamp for display
                record["timestamp_formatted"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            
            return records
        except Exception as e:
            print(f"Error retrieving transcriptions: {e}")
            return []
    
    def get_transcription_by_id(self, record_id: str) -> Optional[Dict]:
        """
        Get a specific transcription record by ID.
        
        Args:
            record_id: The ID of the record to retrieve
            
        Returns:
            The transcription record or None if not found
        """
        try:
            from bson import ObjectId
            record = self.collection.find_one({"_id": ObjectId(record_id)})
            if record:
                record["_id"] = str(record["_id"])
                record["timestamp_formatted"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            return record
        except Exception as e:
            print(f"Error retrieving transcription by ID: {e}")
            return None
    
    def delete_transcription(self, record_id: str) -> bool:
        """
        Delete a transcription record by ID.
        
        Args:
            record_id: The ID of the record to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            from bson import ObjectId
            result = self.collection.delete_one({"_id": ObjectId(record_id)})
            if result.deleted_count > 0:
                print(f"Transcription deleted successfully: {record_id}")
                return True
            else:
                print(f"No transcription found with ID: {record_id}")
                return False
        except Exception as e:
            print(f"Error deleting transcription: {e}")
            return False
    
    def update_transcription(self, record_id: str, updates: Dict) -> bool:
        """
        Update a transcription record.
        
        Args:
            record_id: The ID of the record to update
            updates: Dictionary of fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            from bson import ObjectId
            # Add update timestamp
            updates["updated_at"] = datetime.now()
            
            result = self.collection.update_one(
                {"_id": ObjectId(record_id)},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                print(f"Transcription updated successfully: {record_id}")
                return True
            else:
                print(f"No transcription found with ID: {record_id}")
                return False
        except Exception as e:
            print(f"Error updating transcription: {e}")
            return False
    
    def search_transcriptions(self, query: str) -> List[Dict]:
        """
        Search transcriptions by text content.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching transcription records
        """
        try:
            # Create text index if it doesn't exist
            try:
                self.collection.create_index([("transcript", "text"), ("summary", "text"), ("audio_filename", "text")])
            except:
                pass  # Index might already exist
            
            # Perform text search
            records = list(self.collection.find(
                {"$text": {"$search": query}}
            ).sort("timestamp", -1))
            
            # Convert ObjectId to string for JSON serialization
            for record in records:
                record["_id"] = str(record["_id"])
                record["timestamp_formatted"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            
            return records
        except Exception as e:
            print(f"Error searching transcriptions: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary containing database statistics
        """
        try:
            total_records = self.collection.count_documents({})
            
            # Get model usage statistics
            whisper_models = list(self.collection.aggregate([
                {"$group": {"_id": "$whisper_model", "count": {"$sum": 1}}}
            ]))
            
            llm_models = list(self.collection.aggregate([
                {"$group": {"_id": "$llm_model", "count": {"$sum": 1}}}
            ]))
            
            # Get recent activity (last 7 days)
            from datetime import timedelta
            last_week = datetime.now() - timedelta(days=7)
            recent_records = self.collection.count_documents({"timestamp": {"$gte": last_week}})
            
            return {
                "total_records": total_records,
                "whisper_models": whisper_models,
                "llm_models": llm_models,
                "recent_records": recent_records
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def _get_audio_duration(self, transcript: str) -> int:
        """
        Estimate audio duration from transcript length.
        This is a rough estimation - you might want to store actual duration.
        
        Args:
            transcript: The transcript text
            
        Returns:
            Estimated duration in seconds
        """
        # Rough estimation: average speaking rate is about 150 words per minute
        words = len(transcript.split())
        return int((words / 150) * 60)
    
    def close_connection(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

# Singleton instance
_db_manager = None

def get_database_manager():
    """Get the singleton database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
