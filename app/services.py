"""
External Services Integration
"""
import httpx
from groq import AsyncGroq
from .config import settings
import logging

logger = logging.getLogger(__name__)

class GeocodingService:
    BASE_URL = "https://graphhopper.com/api/1"
    
    @staticmethod
    async def get_address(lat: float, lon: float) -> str:
        if not settings.GRAPHHOPPER_API_KEY:
            return f"{lat}, {lon}"
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{GeocodingService.BASE_URL}/geocode",
                    params={
                        "point": f"{lat},{lon}",
                        "reverse": "true",
                        "key": settings.GRAPHHOPPER_API_KEY,
                        "limit": 1
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("hits"):
                        hit = data["hits"][0]
                        # Construct a readable address from available fields
                        parts = []
                        for field in ["name", "street", "city", "state", "country"]:
                            if field in hit and hit[field]:
                                parts.append(hit[field])
                        return ", ".join(parts) if parts else f"{lat}, {lon}"
                
                logger.warning(f"Geocoding failed: {response.text}")
                return f"{lat}, {lon}"
                
        except Exception as e:
            logger.error(f"Geocoding error: {str(e)}")
            return f"{lat}, {lon}"

class LLMService:
    @staticmethod
    async def generate_trip_story(trip_data: dict, start_address: str, end_address: str) -> str:
        if not settings.GROQ_API_KEY:
            return "LLM API Key not configured. Unable to generate story."
            
        try:
            client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            
            prompt = f"""
            Write a creative and engaging short story (approx 150 words) about a trip based on the following data:
            
            Start Location: {start_address}
            End Location: {end_address}
            Start Time: {trip_data['start_time']}
            End Time: {trip_data['end_time']}
            Duration: {trip_data['duration']}
            
            The story should describe the journey, mentioning the route and implied scenery between these two locations.
            Keep it professional but descriptive.
            """
            
            chat_completion = await client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a travel writer who turns trip data into engaging narratives."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=300,
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            return f"Error generating story: {str(e)}"
