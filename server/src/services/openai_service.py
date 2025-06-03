import os
from openai import OpenAI

class OpenAIService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
    
    def get_track_info(self, track_name, artists, album):
        """Get information about a track using OpenAI."""
        artist_names = ', '.join(artists) if isinstance(artists, list) else artists
        
        prompt = f"""
        Give me interesting information, facts, and background about the song "{track_name}" by {artist_names} from the album "{album}".
        Include details about its creation, reception, musical style, lyrical themes, chart performance, and any interesting trivia.
        Format the response in a conversational, engaging way, like you're enthusiastically sharing this information with a music fan.
        Keep the response concise (maximum 3 paragraphs).
        """
        
        return self._make_openai_request(prompt)
    
    def get_artist_info(self, artist_name, genres=None):
        """Get information about an artist using OpenAI."""
        genre_text = ""
        if genres:
            genre_text = f" Their genres include {', '.join(genres)}."
        
        prompt = f"""
        Give me interesting information and facts about the music artist "{artist_name}".{genre_text}
        Include details about their background, musical style, career highlights, influence on music, notable albums/songs, and any interesting trivia.
        Format the response in a conversational, engaging way, like you're enthusiastically sharing this information with a music fan.
        Keep the response concise (maximum 3 paragraphs).
        """
        
        return self._make_openai_request(prompt)
    
    def get_album_info(self, album_name, artists, release_date=None):
        """Get information about an album using OpenAI."""
        artist_names = ', '.join(artists) if isinstance(artists, list) else artists
        release_info = f" Released in {release_date}." if release_date else ""
        
        prompt = f"""
        Give me interesting information and facts about the album "{album_name}" by {artist_names}.{release_info}
        Include details about its creation, reception, musical style, lyrical themes, chart performance, and any interesting trivia.
        Format the response in a conversational, engaging way, like you're enthusiastically sharing this information with a music fan.
        Keep the response concise (maximum 3 paragraphs).
        """
        
        return self._make_openai_request(prompt)
    
    def _make_openai_request(self, prompt):
        """Make a request to the OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable music expert providing concise information about songs, artists, and albums."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
