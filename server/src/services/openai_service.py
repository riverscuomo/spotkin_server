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
        Provide information about "{track_name}" by {artist_names} from "{album}".
        Include factual details about its creation, reception, style, and themes if available.
        If you know any verified anecdotes about the track, include them, but DON'T make anything up.
        Present the information in a straightforward, factual manner without exaggeration.
        Keep it brief (max 2 paragraphs).
        """
        
        return self._make_openai_request(prompt)
    
    def get_artist_info(self, artist_name, genres=None):
        """Get information about an artist using OpenAI."""
        genre_text = ""
        if genres:
            genre_text = f" Their genres include {', '.join(genres)}."
        
        prompt = f"""
        Provide information about "{artist_name}".{genre_text}
        Cover their background, style, works, and factual information about their career.
        If you know any verified anecdotes, include them, but DON'T make anything up.
        Present the information in a straightforward, factual manner without exaggeration.
        Keep it brief (max 2 paragraphs).
        """
        
        return self._make_openai_request(prompt)
    
    def get_album_info(self, album_name, artists, release_date=None):
        """Get information about an album using OpenAI."""
        artist_names = ', '.join(artists) if isinstance(artists, list) else artists
        release_info = f" Released in {release_date}." if release_date else ""
        
        prompt = f"""
        Provide information about "{album_name}" by {artist_names}.{release_info}
        Include factual details about its creation, reception, style, and themes if available.
        If you know any verified anecdotes about the album or recording process, include them, but DON'T make anything up.
        Present the information in a straightforward, factual manner without exaggeration.
        Keep it brief (max 2 paragraphs).
        """
        
        return self._make_openai_request(prompt)
    
    def _make_openai_request(self, prompt):
        """Make a request to the OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You're a music information provider. Present factual information without unnecessary hype. Focus on accuracy and clarity."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
