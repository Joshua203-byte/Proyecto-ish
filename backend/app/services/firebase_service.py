import firebase_admin
from firebase_admin import credentials, storage
import json
import os
import uuid
from app.config import settings

class FirebaseService:
    _initialized = False

    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK."""
        if cls._initialized:
            return

        try:
            # Check if credentials JSON is provided via env var
            if settings.FIREBASE_CREDENTIALS_JSON:
                cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                cred = credentials.Certificate(cred_dict)
            else:
                # Fallback to local file (dev mode)
                cred = credentials.Certificate("serviceAccountKey.json")

            firebase_admin.initialize_app(cred, {
                'storageBucket': settings.FIREBASE_STORAGE_BUCKET
            })
            cls._initialized = True
            print("✅ Firebase Admin Initialized")
        except Exception as e:
            print(f"⚠️ Failed to initialize Firebase: {e}")

    def upload_file(self, file, destination_path: str, content_type: str = None) -> str:
        """
        Uploads a file-like object to Firebase Storage.
        Returns the public URL.
        """
        try:
            bucket = storage.bucket()
            blob = bucket.blob(destination_path)
            
            # Upload from file object
            blob.upload_from_file(file, content_type=content_type)
            
            # Make public
            blob.make_public()
            
            return blob.public_url
        except Exception as e:
            print(f"❌ Firebase Upload Error: {e}")
            raise e

    def delete_file(self, path: str):
        """Deletes a file from Firebase Storage."""
        try:
            bucket = storage.bucket()
            blob = bucket.blob(path)
            blob.delete()
        except Exception as e:
            print(f"⚠️ Firebase Delete Error: {e}")
