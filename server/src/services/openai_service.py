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
        Give me the essential info about "{track_name}" by {artist_names} from "{album}".
        Include key details on its creation, reception, style, themes, and any notable trivia.
        Share any interesting insider anecdotes about the track if you know them, but DON'T make anything up.
        Format the response like a knowledgeable older friend or uncle - straight-talking, insightful, and confident without being overly enthusiastic.
        Keep it brief (max 2 paragraphs).
        """
        
        return self._make_openai_request(prompt)
    
    def get_artist_info(self, artist_name, genres=None):
        """Get information about an artist using OpenAI."""
        genre_text = ""
        if genres:
            genre_text = f" Their genres include {', '.join(genres)}."
        
        prompt = f"""
        Break down what makes "{artist_name}" significant.{genre_text}
        Cover their background, style, major achievements, industry influence, and key works.
        Include any interesting insider anecdotes or behind-the-scenes stories if you know them, but DON'T make anything up.
        Format the response like a knowledgeable older friend or uncle - straight-talking, insightful, and confident without unnecessary hype.
        Keep it brief (max 2 paragraphs).
        """
        
        return self._make_openai_request(prompt)
    
    def get_album_info(self, album_name, artists, release_date=None):
        """Get information about an album using OpenAI."""
        artist_names = ', '.join(artists) if isinstance(artists, list) else artists
        release_info = f" Released in {release_date}." if release_date else ""
        
        prompt = f"""
        What's the deal with "{album_name}" by {artist_names}?{release_info}
        Cover its creation, reception, style, themes, impact, and any standout facts.
        Share any interesting insider anecdotes about the album or recording process if you know them, but DON'T make anything up.
        Format the response like a knowledgeable older friend or uncle - straight-talking, insightful, and confident without unnecessary enthusiasm.
        Keep it brief (max 2 paragraphs).
        """
        
        return self._make_openai_request(prompt)
    
    def _make_openai_request(self, prompt):
        """Make a request to the OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You're a music expert who talks like a cool, knowledgeable older brother/uncle. Be insightful but not verbose. Focus on substance over style."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
