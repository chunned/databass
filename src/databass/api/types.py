from datetime import date
from typing import TypedDict, Optional

class EntityInfo(TypedDict, total=False):
    name: str
    mbid: str
    begin_date: Optional[date]
    end_date: Optional[date]
    country: Optional[str]
    type: Optional[str]

class ArtistInfo(EntityInfo):
    pass

class LabelInfo(EntityInfo):
    pass

class ReleaseInfo(TypedDict, total=False):
    release: dict[str, str]
    artist: dict[str, str]
    label: dict[str, str]
    date: str
    format: str
    track_count: str
    country: str
    release_group_id: str

class SearchResult(TypedDict, total=False):
    name: str
    id: str
    life_span: dict[str, str]
    country: str
    type: str
