"""Semantic field type detection using embeddings."""

from typing import List, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np


class SemanticFieldDetector:
    """Detects field types using semantic similarity with embeddings."""

    # Common field types with semantic keywords
    FIELD_TYPE_KEYWORDS = {
        "email": [
            "email",
            "e-mail",
            "mail",
            "email_address",
            "user_email",
            "contact_email",
        ],
        "name": [
            "name",
            "full_name",
            "fullname",
            "user_name",
            "username",
            "first_name",
            "last_name",
            "person_name",
        ],
        "phone": [
            "phone",
            "telephone",
            "mobile",
            "phone_number",
            "tel",
            "contact_number",
            "cell",
            "cellphone",
        ],
        "address": [
            "address",
            "street",
            "location",
            "street_address",
            "home_address",
            "postal_address",
        ],
        "city": ["city", "town", "municipality", "locality"],
        "country": [
            "country",
            "nation",
            "country_name",
            "country_code",
        ],
        "zipcode": [
            "zip",
            "zipcode",
            "postal_code",
            "postcode",
            "zip_code",
        ],
        "date": [
            "date",
            "created_at",
            "updated_at",
            "birth_date",
            "birthday",
            "timestamp",
        ],
        "url": [
            "url",
            "website",
            "link",
            "homepage",
            "web_address",
            "uri",
        ],
        "company": [
            "company",
            "organization",
            "employer",
            "business",
            "company_name",
        ],
        "job": ["job", "occupation", "position", "role", "job_title", "title"],
        "price": [
            "price",
            "cost",
            "amount",
            "total",
            "subtotal",
            "fee",
            "charge",
        ],
        "id": [
            "id",
            "identifier",
            "uuid",
            "guid",
            "key",
            "primary_key",
            "user_id",
        ],
        "description": [
            "description",
            "desc",
            "details",
            "summary",
            "notes",
            "comment",
        ],
        "boolean": [
            "is_active",
            "is_enabled",
            "is_valid",
            "active",
            "enabled",
            "flag",
        ],
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", similarity_threshold: float = 0.6):
        """
        Initialize semantic field detector.

        Args:
            model_name: Sentence transformer model name
            similarity_threshold: Minimum cosine similarity to consider a match
        """
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        self._field_type_embeddings = self._compute_field_type_embeddings()

    def _compute_field_type_embeddings(self) -> dict:
        """Pre-compute embeddings for all field type keywords."""
        embeddings = {}
        for field_type, keywords in self.FIELD_TYPE_KEYWORDS.items():
            # Average embeddings of all keywords for this field type
            keyword_embeddings = self.model.encode(keywords)
            avg_embedding = np.mean(keyword_embeddings, axis=0)
            embeddings[field_type] = avg_embedding
        return embeddings

    def detect_field_type(
        self, field_name: str, sample_values: Optional[List[str]] = None
    ) -> Tuple[Optional[str], float]:
        """
        Detect field type based on field name and optional sample values.

        Args:
            field_name: The name of the field
            sample_values: Optional sample values to aid detection

        Returns:
            Tuple of (detected_type, confidence_score)
        """
        # Encode the field name
        field_embedding = self.model.encode([field_name])[0]

        # Calculate cosine similarity with each field type
        similarities = {}
        for field_type, type_embedding in self._field_type_embeddings.items():
            similarity = self._cosine_similarity(field_embedding, type_embedding)
            similarities[field_type] = similarity

        # Get the best match
        best_match = max(similarities.items(), key=lambda x: x[1])
        field_type, confidence = best_match

        # Return None if confidence is below threshold
        if confidence < self.similarity_threshold:
            return None, confidence

        return field_type, confidence

    def detect_multiple_fields(
        self, fields: List[Tuple[str, Optional[List[str]]]]
    ) -> List[Tuple[str, Optional[str], float]]:
        """
        Detect types for multiple fields at once.

        Args:
            fields: List of (field_name, sample_values) tuples

        Returns:
            List of (field_name, detected_type, confidence) tuples
        """
        results = []
        for field_name, sample_values in fields:
            detected_type, confidence = self.detect_field_type(field_name, sample_values)
            results.append((field_name, detected_type, confidence))
        return results

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def get_field_suggestions(self, field_name: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Get top K field type suggestions for a given field name.

        Args:
            field_name: The name of the field
            top_k: Number of suggestions to return

        Returns:
            List of (field_type, confidence) tuples sorted by confidence
        """
        field_embedding = self.model.encode([field_name])[0]

        similarities = []
        for field_type, type_embedding in self._field_type_embeddings.items():
            similarity = self._cosine_similarity(field_embedding, type_embedding)
            similarities.append((field_type, similarity))

        # Sort by similarity and return top K
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
